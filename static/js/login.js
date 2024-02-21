// Função para exibir a mensagem de erro
function showErrorPopup(message) {
    const popup = document.getElementById('error-popup');
    popup.innerText = message;
    popup.style.display = 'block';

    // Automatically hide the error message after a few seconds (adjust the timeout value as needed)
    setTimeout(() => {
        popup.style.display = 'none';
    }, 3000); // Hide after 3 seconds (adjust as needed)
}
// Verifique se a URL atual possui o parâmetro de erro
const urlParams = new URLSearchParams(window.location.search);
const erro = urlParams.get('erro');
// Verifique se há um parâmetro de erro e exiba a mensagem de erro correspondente
if (erro === 'credenciais_invalidas') {
    exibirMensagemErro();
}

document.querySelector('.back-form-btn').addEventListener('click', function(event) {
    event.preventDefault();
    window.location.href = 'http://127.0.0.1:5000/';
});

let inputs = document.getElementsByClassName("input-form");
for (let input of inputs) {
    input.addEventListener("blur", function () {
        if (input.value.trim() != "") {
            input.classList.add("has-val");
        } else {
            input.classList.remove("has-val");
        }
    });
}