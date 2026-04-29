document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const usernameError = document.getElementById('username-error');
    const passwordError = document.getElementById('password-error');

    if (!loginForm || !usernameInput || !passwordInput) return;

    // Handle custom placeholder visibility
    const togglePlaceholder = (input, placeholder) => {
        if (!placeholder) return;
        if (input.value.length > 0) {
            placeholder.style.opacity = '0';
        } else {
            placeholder.style.opacity = '1';
        }
    };

    const userPlaceholder = document.getElementById('user-placeholder');
    const passPlaceholder = document.getElementById('pass-placeholder');

    const clearInputError = (input, errorElement) => {
        if (input.parentElement) input.parentElement.classList.remove('error');
        if (errorElement) errorElement.style.display = 'none';
    };

    usernameInput.addEventListener('input', () => {
        togglePlaceholder(usernameInput, userPlaceholder);
        clearInputError(usernameInput, usernameError);
    });
    passwordInput.addEventListener('input', () => {
        togglePlaceholder(passwordInput, passPlaceholder);
        clearInputError(passwordInput, passwordError);
    });

    const showError = (input, errorElement, message) => {
        if (input.parentElement) input.parentElement.classList.add('error');
        if (errorElement) {
            errorElement.textContent = message;
            errorElement.style.display = 'block';
        } else {
            // Fallback if error element is missing
            input.setCustomValidity(message);
            input.reportValidity();
        }
    };

    const clearErrors = () => {
        clearInputError(usernameInput, usernameError);
        clearInputError(passwordInput, passwordError);
        usernameInput.setCustomValidity('');
        passwordInput.setCustomValidity('');
    };

    // Login Submission
    loginForm.addEventListener('submit', (e) => {
        // Only prevent default if we have errors to show
        const username = usernameInput.value.trim();
        const password = passwordInput.value;

        clearErrors();

        let hasError = false;
        if (!username) {
            showError(usernameInput, usernameError, 'Vui lòng nhập tên đăng nhập');
            hasError = true;
        }
        if (!password) {
            showError(passwordInput, passwordError, 'Vui lòng nhập mật khẩu');
            hasError = true;
        }
        
        if (hasError) {
            e.preventDefault();
        }
    });

    // Check initial values (in case browser autofills)
    setTimeout(() => {
        togglePlaceholder(usernameInput, userPlaceholder);
        togglePlaceholder(passwordInput, passPlaceholder);
    }, 100);
});
