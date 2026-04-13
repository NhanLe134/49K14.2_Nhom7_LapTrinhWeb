document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const usernameError = document.getElementById('username-error');
    const passwordError = document.getElementById('password-error');

    // Handle custom placeholder visibility
    const togglePlaceholder = (input, placeholder) => {
        if (input.value.length > 0) {
            placeholder.style.opacity = '0';
        } else {
            placeholder.style.opacity = '1';
        }
    };

    const userPlaceholder = document.getElementById('user-placeholder');
    const passPlaceholder = document.getElementById('pass-placeholder');

    const clearInputError = (input, errorElement) => {
        input.parentElement.classList.remove('error');
        errorElement.style.display = 'none';
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
        input.parentElement.classList.add('error');
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    };

    const clearErrors = () => {
        clearInputError(usernameInput, usernameError);
        clearInputError(passwordInput, passwordError);
    };

    // Login Submission
    loginForm.addEventListener('submit', (e) => {
        e.preventDefault();

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
        
        if (!hasError) {
            // Form is valid, submit to Django backend
            loginForm.submit();
        }
    });

    // Check initial values (in case browser autofills)
    setTimeout(() => {
        togglePlaceholder(usernameInput, userPlaceholder);
        togglePlaceholder(passwordInput, passPlaceholder);
    }, 100);
});
