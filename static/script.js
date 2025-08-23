document.addEventListener('DOMContentLoaded', function() {
    // Tab switching functionality
    const tabButtons = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', () => {
            const tabId = button.getAttribute('data-tab');
            
            // Hide all tab contents
            tabContents.forEach(content => {
                content.classList.remove('active');
            });
            
            // Deactivate all buttons
            tabButtons.forEach(btn => {
                btn.classList.remove('active');
            });
            
            // Show selected tab content
            document.getElementById(tabId).classList.add('active');
            button.classList.add('active');
        });
    });

    // Form validation for registration
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function(e) {
            let isValid = true;
            
            // Validate username
            const username = document.getElementById('username');
            if (username.value.trim().length < 3) {
                document.getElementById('usernameError').style.display = 'block';
                isValid = false;
            } else {
                document.getElementById('usernameError').style.display = 'none';
            }
            
            // Validate password
            const password = document.getElementById('password');
            if (password.value.length < 8) {
                document.getElementById('passwordError').style.display = 'block';
                isValid = false;
            } else {
                document.getElementById('passwordError').style.display = 'none';
            }
            
            // Validate password confirmation
            const confirmPassword = document.getElementById('confirmPassword');
            if (password.value !== confirmPassword.value) {
                document.getElementById('confirmPasswordError').style.display = 'block';
                isValid = false;
            } else {
                document.getElementById('confirmPasswordError').style.display = 'none';
            }
            
            // Validate email
            const email = document.getElementById('email');
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(email.value)) {
                document.getElementById('emailError').style.display = 'block';
                isValid = false;
            } else {
                document.getElementById('emailError').style.display = 'none';
            }
            
            // Validate mobile
            const mobile = document.getElementById('mobile');
            if (mobile.value.length < 10) {
                document.getElementById('mobileError').style.display = 'block';
                isValid = false;
            } else {
                document.getElementById('mobileError').style.display = 'none';
            }
            
            // Validate terms
            const terms = document.getElementById('terms');
            if (!terms.checked) {
                document.getElementById('termsError').style.display = 'block';
                isValid = false;
            } else {
                document.getElementById('termsError').style.display = 'none';
            }
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    }

    // Food request modal functionality
    const requestButtons = document.querySelectorAll('.request-btn');
    const requestModal = document.getElementById('requestModal');
    const closeModal = document.getElementById('closeModal');
    
    if (requestButtons && requestModal) {
        requestButtons.forEach(button => {
            button.addEventListener('click', function() {
                const foodId = this.getAttribute('data-id');
                
                // Fetch food details (in a real app, you would make an API call)
                fetch(`/api/food/${foodId}`)
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('modalFoodName').textContent = data.food_name;
                        document.getElementById('modalFoodQuantity').textContent = `Available Quantity: ${data.quantity}`;
                        document.getElementById('modalFoodAddress').textContent = `Pickup Location: ${data.pickup_address}`;
                        document.getElementById('modalFoodExpiry').textContent = `Best Before: ${data.expiry_date}`;
                        document.getElementById('requestFoodId').value = foodId;
                        requestModal.classList.remove('hidden');
                    });
            });
        });
        
        closeModal.addEventListener('click', function() {
            requestModal.classList.add('hidden');
        });
    }

    // Display success messages and fade them out
    const successMessages = document.querySelectorAll('.alert-success');
    successMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 500);
        }, 3000);
    });

    // Display error messages and fade them out
    const errorMessages = document.querySelectorAll('.alert-danger');
    errorMessages.forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => {
                message.remove();
            }, 500);
        }, 5000);
    });

    // Volunteer action buttons
    const volunteerActions = document.querySelectorAll('.volunteer-action');
    volunteerActions.forEach(button => {
        button.addEventListener('click', function() {
            const requestId = this.getAttribute('data-id');
            const action = this.getAttribute('data-action');
            
            fetch('/volunteer', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `request_id=${requestId}&action=${action}`
            })
            .then(response => {
                if (response.ok) {
                    window.location.reload();
                }
            });
        });
    });

    // Auto-expire food items that are past their expiry date
    function checkExpiredFoods() {
        fetch('/api/foods/expired')
            .then(response => response.json())
            .then(data => {
                if (data.expiredCount > 0) {
                    // Update the UI if needed
                }
            });
    }
    
    // Check every 30 minutes
    setInterval(checkExpiredFoods, 1800000);
    checkExpiredFoods();
});
