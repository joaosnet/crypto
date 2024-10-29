document.addEventListener('DOMContentLoaded', function() {
    const mathField = document.getElementById('mathlive-input');

    // Evento de foco para exibir o teclado virtual
    mathField.addEventListener('focusin', function() {
        mathField.executeCommand('showVirtualKeyboard');
    });

    // Esconde o teclado ao clicar fora do math-field
    mathField.addEventListener('focusout', function(event) {
        if (!mathField.contains(event.target)) {
            mathField.executeCommand('hideVirtualKeyboard');
        }
    });
});