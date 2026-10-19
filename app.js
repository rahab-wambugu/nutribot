document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('diabetes-form');
    const submitBtn = document.getElementById('submit-btn');
    const resultsContainer = document.getElementById('results-container');
    
    // Safety check: ensure the main form exists before adding listeners
    if (!form) {
        console.error("Error: Could not find element with id 'diabetes-form' in index.html");
        return;
    }

    const btnText = submitBtn ? submitBtn.querySelector('.btn-text') : null;
    const spinner = submitBtn ? submitBtn.querySelector('.spinner') : null;
    
    // Output containers
    const exerciseOutput = document.getElementById('exercise-output');
    const mealOutput = document.getElementById('meal-output');
    const analysisOutput = document.getElementById('analysis-output');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const bloodSugarInput = document.getElementById('blood-sugar');
        const timingInput = document.getElementById('timing');
        const mealPlanInput = document.getElementById('meal-plan');

        const formData = {
            bloodSugar: bloodSugarInput ? bloodSugarInput.value : '',
            timing: timingInput ? timingInput.value : '',
            mealPlan: mealPlanInput ? mealPlanInput.value : ''
        };

        // Update UI to Loading State safely
        if (submitBtn) submitBtn.disabled = true;
        if (btnText) btnText.textContent = 'Analyzing Inputs...';
        if (spinner) spinner.classList.remove('hidden');
        if (resultsContainer) resultsContainer.classList.add('hidden');

        try {
            const response = await fetch('http://localhost:8000/api/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();

            // Populate results safely
            if (exerciseOutput) exerciseOutput.textContent = data.exercise;
            if (mealOutput) mealOutput.textContent = data.meal;
            if (analysisOutput) analysisOutput.textContent = data.analysis;
            
            if (resultsContainer) {
                resultsContainer.classList.remove('hidden');
                resultsContainer.scrollIntoView({ behavior: 'smooth' });
            }

        } catch (error) {
            console.error('Error fetching recommendations:', error);
            alert('Communication error with Python backend. Ensure uvicorn is running.');
        } finally {
            // Reset Button State safely
            if (submitBtn) submitBtn.disabled = false;
            if (btnText) btnText.textContent = 'Generate Recommendations';
            if (spinner) spinner.classList.add('hidden');
        }
    });
    
});
