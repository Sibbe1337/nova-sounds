/**
 * Form Validator
 * Standardized form validation with live feedback
 */

// Default validation messages
const DEFAULT_MESSAGES = {
    required: 'This field is required',
    email: 'Please enter a valid email address',
    url: 'Please enter a valid URL',
    minLength: (min) => `Please enter at least ${min} characters`,
    maxLength: (max) => `Please enter no more than ${max} characters`,
    pattern: 'Please enter a valid value',
    match: 'Fields do not match',
    number: 'Please enter a valid number',
    min: (min) => `Please enter a value greater than or equal to ${min}`,
    max: (max) => `Please enter a value less than or equal to ${max}`
};

// Default validation patterns
const DEFAULT_PATTERNS = {
    email: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
    url: /^(https?:\/\/)?(www\.)?[-a-zA-Z0-9@:%._\+~#=]{2,256}\.[a-z]{2,6}\b([-a-zA-Z0-9@:%_\+.~#?&//=]*)$/,
    alphanumeric: /^[a-zA-Z0-9]+$/,
    numeric: /^[0-9]+$/,
    phone: /^[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}$/
};

// Keep track of all validators
const formValidators = new Map();

/**
 * Create a validator for a form element
 * @param {string|Element} form - Form element or selector
 * @param {Object} options - Validator options
 * @returns {Object} - Validator object
 */
function createValidator(form, options = {}) {
    // Get form element
    if (typeof form === 'string') {
        form = document.querySelector(form);
    }
    
    if (!form) {
        console.error('Form element not found');
        return null;
    }
    
    const {
        validateOnInput = true,
        validateOnBlur = true,
        validateOnSubmit = true,
        scrollToError = true,
        errorClass = 'error',
        successClass = 'success',
        errorMessageClass = 'error-message',
        fieldSelector = '[data-validate]',
        customMessages = {},
        customValidators = {}
    } = options;
    
    // Messages - merge defaults with custom
    const messages = { ...DEFAULT_MESSAGES, ...customMessages };
    
    // Get all fields with data-validate attribute
    const fields = Array.from(form.querySelectorAll(fieldSelector));
    
    // Set up validation state
    const formState = {
        valid: true,
        errors: {},
        values: {}
    };
    
    // Initialize the form
    function init() {
        // Set up event listeners
        if (validateOnInput) {
            fields.forEach(field => {
                field.addEventListener('input', () => validateField(field));
            });
        }
        
        if (validateOnBlur) {
            fields.forEach(field => {
                field.addEventListener('blur', () => validateField(field));
            });
        }
        
        if (validateOnSubmit) {
            form.addEventListener('submit', handleSubmit);
        }
        
        // Store validator for this form
        formValidators.set(form, validator);
    }
    
    // Handle form submission
    function handleSubmit(event) {
        const isValid = validateAll();
        
        if (!isValid) {
            event.preventDefault();
            
            // Focus first field with error
            const firstErrorField = form.querySelector(`.${errorClass}`);
            if (firstErrorField) {
                if (scrollToError) {
                    firstErrorField.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                }
                
                firstErrorField.focus();
            }
        }
    }
    
    // Validate a single field
    function validateField(field) {
        const name = field.name || field.id;
        const value = field.value.trim();
        const validations = getValidations(field);
        let isValid = true;
        let errorMessage = '';
        
        // Store the value in formState
        formState.values[name] = value;
        
        // Check required
        if (validations.required && value === '') {
            isValid = false;
            errorMessage = messages.required;
        }
        // Only continue validation if field has a value or is required
        else if (value !== '' || validations.required) {
            // Check min length
            if (validations.minLength && value.length < validations.minLength) {
                isValid = false;
                errorMessage = typeof messages.minLength === 'function' 
                    ? messages.minLength(validations.minLength)
                    : messages.minLength;
            }
            
            // Check max length
            if (isValid && validations.maxLength && value.length > validations.maxLength) {
                isValid = false;
                errorMessage = typeof messages.maxLength === 'function'
                    ? messages.maxLength(validations.maxLength)
                    : messages.maxLength;
            }
            
            // Check pattern
            if (isValid && validations.pattern) {
                const pattern = validations.pattern instanceof RegExp
                    ? validations.pattern
                    : DEFAULT_PATTERNS[validations.pattern] || new RegExp(validations.pattern);
                
                if (!pattern.test(value)) {
                    isValid = false;
                    errorMessage = validations.patternMessage || messages.pattern;
                }
            }
            
            // Check email format
            if (isValid && validations.type === 'email' && !DEFAULT_PATTERNS.email.test(value)) {
                isValid = false;
                errorMessage = messages.email;
            }
            
            // Check URL format
            if (isValid && validations.type === 'url' && !DEFAULT_PATTERNS.url.test(value)) {
                isValid = false;
                errorMessage = messages.url;
            }
            
            // Check numeric format
            if (isValid && validations.type === 'number') {
                const numValue = parseFloat(value);
                if (isNaN(numValue)) {
                    isValid = false;
                    errorMessage = messages.number;
                } else {
                    // Check min value
                    if (validations.min !== undefined && numValue < validations.min) {
                        isValid = false;
                        errorMessage = typeof messages.min === 'function'
                            ? messages.min(validations.min)
                            : messages.min;
                    }
                    
                    // Check max value
                    if (isValid && validations.max !== undefined && numValue > validations.max) {
                        isValid = false;
                        errorMessage = typeof messages.max === 'function'
                            ? messages.max(validations.max)
                            : messages.max;
                    }
                }
            }
            
            // Check match with other field
            if (isValid && validations.match) {
                const matchField = form.querySelector(`[name="${validations.match}"], #${validations.match}`);
                if (matchField && matchField.value !== value) {
                    isValid = false;
                    errorMessage = messages.match;
                }
            }
            
            // Run custom validators
            if (isValid && validations.custom) {
                const customValidator = customValidators[validations.custom];
                if (typeof customValidator === 'function') {
                    const result = customValidator(value, field, form);
                    if (result !== true) {
                        isValid = false;
                        errorMessage = result || `Validation failed: ${validations.custom}`;
                    }
                }
            }
        }
        
        // Update field UI state
        updateFieldState(field, isValid, errorMessage);
        
        // Update form state
        if (!isValid) {
            formState.errors[name] = errorMessage;
        } else {
            delete formState.errors[name];
        }
        
        // Update overall form validity
        formState.valid = Object.keys(formState.errors).length === 0;
        
        return isValid;
    }
    
    // Get validations for a field from its attributes
    function getValidations(field) {
        const validations = {};
        
        // Parse data-validate attribute for validation rules
        const validateAttr = field.getAttribute('data-validate');
        if (validateAttr) {
            validateAttr.split(',').forEach(rule => {
                const trimmedRule = rule.trim();
                if (trimmedRule === 'required') {
                    validations.required = true;
                } else if (trimmedRule.startsWith('minLength:')) {
                    validations.minLength = parseInt(trimmedRule.split(':')[1]);
                } else if (trimmedRule.startsWith('maxLength:')) {
                    validations.maxLength = parseInt(trimmedRule.split(':')[1]);
                } else if (trimmedRule.startsWith('pattern:')) {
                    validations.pattern = trimmedRule.split(':')[1];
                } else if (trimmedRule.startsWith('match:')) {
                    validations.match = trimmedRule.split(':')[1];
                } else if (trimmedRule.startsWith('type:')) {
                    validations.type = trimmedRule.split(':')[1];
                } else if (trimmedRule.startsWith('min:')) {
                    validations.min = parseFloat(trimmedRule.split(':')[1]);
                } else if (trimmedRule.startsWith('max:')) {
                    validations.max = parseFloat(trimmedRule.split(':')[1]);
                } else if (trimmedRule.startsWith('custom:')) {
                    validations.custom = trimmedRule.split(':')[1];
                }
            });
        }
        
        // Check for required attribute
        if (field.required) {
            validations.required = true;
        }
        
        // Check input type
        if (field.type === 'email') {
            validations.type = 'email';
        } else if (field.type === 'url') {
            validations.type = 'url';
        } else if (field.type === 'number') {
            validations.type = 'number';
            
            // Check for min/max attributes
            if (field.hasAttribute('min')) {
                validations.min = parseFloat(field.getAttribute('min'));
            }
            if (field.hasAttribute('max')) {
                validations.max = parseFloat(field.getAttribute('max'));
            }
        }
        
        // Check for minlength/maxlength attributes
        if (field.hasAttribute('minlength')) {
            validations.minLength = parseInt(field.getAttribute('minlength'));
        }
        if (field.hasAttribute('maxlength')) {
            validations.maxLength = parseInt(field.getAttribute('maxlength'));
        }
        
        // Check for pattern attribute
        if (field.hasAttribute('pattern')) {
            validations.pattern = new RegExp(field.getAttribute('pattern'));
        }
        
        return validations;
    }
    
    // Update field UI state based on validation
    function updateFieldState(field, isValid, errorMessage = '') {
        // Remove existing classes and error messages
        field.classList.remove(errorClass, successClass);
        
        const parentEl = field.closest('.form-group') || field.parentNode;
        const existingError = parentEl.querySelector(`.${errorMessageClass}`);
        if (existingError) {
            existingError.remove();
        }
        
        // Add appropriate class
        field.classList.add(isValid ? successClass : errorClass);
        
        // Add error message if invalid
        if (!isValid) {
            const errorEl = document.createElement('div');
            errorEl.className = errorMessageClass;
            errorEl.textContent = errorMessage;
            
            // Insert after field or at end of parent
            if (field.nextSibling) {
                parentEl.insertBefore(errorEl, field.nextSibling);
            } else {
                parentEl.appendChild(errorEl);
            }
        }
        
        // Update any associated labels
        const labelFor = field.id;
        if (labelFor) {
            const label = document.querySelector(`label[for="${labelFor}"]`);
            if (label) {
                label.classList.remove(errorClass, successClass);
                if (!isValid) {
                    label.classList.add(errorClass);
                }
            }
        }
    }
    
    // Validate all fields in the form
    function validateAll() {
        let isValid = true;
        
        fields.forEach(field => {
            const fieldValid = validateField(field);
            isValid = isValid && fieldValid;
        });
        
        return isValid;
    }
    
    // Reset the form validation state
    function reset() {
        fields.forEach(field => {
            field.classList.remove(errorClass, successClass);
            
            const parentEl = field.closest('.form-group') || field.parentNode;
            const existingError = parentEl.querySelector(`.${errorMessageClass}`);
            if (existingError) {
                existingError.remove();
            }
        });
        
        formState.valid = true;
        formState.errors = {};
        formState.values = {};
    }
    
    // Validator object exposed to the outside
    const validator = {
        form,
        fields,
        validateField,
        validateAll,
        reset,
        state: formState
    };
    
    // Initialize
    init();
    
    return validator;
}

// Initialize validators for forms with the `data-form-validate` attribute
document.addEventListener('DOMContentLoaded', () => {
    const forms = document.querySelectorAll('form[data-form-validate]');
    
    forms.forEach(form => {
        createValidator(form);
    });
});

// Export the API
window.FormValidator = {
    create: createValidator,
    getValidator: (form) => {
        if (typeof form === 'string') {
            form = document.querySelector(form);
        }
        return form ? formValidators.get(form) : null;
    },
    patterns: DEFAULT_PATTERNS
}; 