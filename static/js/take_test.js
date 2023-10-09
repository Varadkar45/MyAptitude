document.addEventListener('DOMContentLoaded', function() {
    const test_name = "{{ test_name }}"; // Replace with your actual test name
    
    let currentQuestionIndex = 0;
    let totalQuestions = 0;

    // Function to load and display the next question
    function loadNextQuestion() {
        // Make an AJAX request to load the next question
        fetch(`/load_next_question/${test_name}/${currentQuestionIndex}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    console.error(data.error);
                    return;
                }

                // Update the question number, total questions, and question text
                currentQuestionIndex += 1;
                document.getElementById('question-number').textContent = currentQuestionIndex;
                document.getElementById('total-questions').textContent = totalQuestions;
                document.getElementById('question-text').textContent = data.question_text;

                // Clear previous answer options (if any)
                const answerOptionsElement = document.getElementById('answer-options');
                answerOptionsElement.innerHTML = '';

                // Populate the answer options (construct radio buttons or other elements)
                data.answer_options.forEach((option, index) => {
                    const input = document.createElement('input');
                    input.type = 'radio';
                    input.name = 'selected_answer';
                    input.value = option;
                    input.id = `option${index + 1}`;

                    const label = document.createElement('label');
                    label.htmlFor = `option${index + 1}`;
                    label.textContent = option;

                    answerOptionsElement.appendChild(input);
                    answerOptionsElement.appendChild(label);
                });
            })
            .catch(error => {
                console.error('Error loading next question:', error);
            });
    }

    // Initial load of the first question
    loadNextQuestion();

    // Event listener for the "Next Question" button
    document.getElementById('next-question').addEventListener('click', function(event) {
        event.preventDefault();
        loadNextQuestion();
    });
    
    // Event listener for form submission (to submit answers)
    document.getElementById('answer-form').addEventListener('submit', function(event) {
        event.preventDefault();
        
        // Handle answer submission here (e.g., validate and send to the server)
        const selectedAnswer = document.querySelector('input[name="selected_answer"]:checked');
        if (!selectedAnswer) {
            alert('Please select an answer.');
            return;
        }
        
        const answer = selectedAnswer.value;
        console.log('Selected answer:', answer);
        
        // You can send the selected answer to the server if needed
    });
});
