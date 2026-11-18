// Main JavaScript for AI Calories & Nutrition Web Application

document.addEventListener('DOMContentLoaded', () => {
    // Auto dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {}
        }, 5000);
    });

    // Image upload preview handler
    const foodFileInput = document.getElementById('food_image');
    const imagePreview = document.getElementById('imagePreview');
    const uploadPlaceholder = document.getElementById('uploadPlaceholder');

    if (foodFileInput && imagePreview) {
        foodFileInput.addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    imagePreview.src = event.target.result;
                    imagePreview.classList.remove('d-none');
                    if (uploadPlaceholder) uploadPlaceholder.classList.add('d-none');
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Dynamic BMI Calculator helper on form change if height & weight exist
    const heightInput = document.getElementById('height');
    const weightInput = document.getElementById('weight');
    const bmiBadge = document.getElementById('bmiDisplay');

    function updateBmi() {
        if (!heightInput || !weightInput || !bmiBadge) return;
        const h = parseFloat(heightInput.value) / 100.0;
        const w = parseFloat(weightInput.value);
        if (h > 0.5 && w > 10) {
            const bmi = (w / (h * h)).toFixed(1);
            let category = "Normal";
            let color = "text-success";
            if (bmi < 18.5) { category = "Underweight"; color = "text-primary"; }
            else if (bmi >= 25 && bmi < 30) { category = "Overweight"; color = "text-warning"; }
            else if (bmi >= 30) { category = "Obese"; color = "text-danger"; }

            bmiBadge.innerHTML = `Calculated BMI: <strong>${bmi}</strong> &bull; <span class="${color}">${category}</span>`;
            bmiBadge.className = "form-text text-muted mt-1";
        }
    }

    if (heightInput && weightInput) {
        heightInput.addEventListener('input', updateBmi);
        weightInput.addEventListener('input', updateBmi);
        updateBmi(); // Run on initial load
    }
});
