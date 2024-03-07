document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.photo img').forEach(item => {
        item.addEventListener('click', event => {
            const modal = document.getElementById("imageModal");
            const modalImg = document.getElementById("img"); // ID corrigido aqui
            const captionText = document.getElementById("caption");
            const imageInfo = document.getElementById("imageInfo");
            const downloadLink = document.getElementById("downloadLink");

            modal.style.display = "block";
            modalImg.src = item.src;
            captionText.innerHTML = item.alt; // Ou qualquer outra informação
            imageInfo.innerHTML = "Detalhes da Imagem"; // Substitua com informações reais da imagem
            downloadLink.href = item.src; // Define o link para download

            // Fechar o modal
            const span = document.getElementsByClassName("close")[0];
            span.onclick = function() {
                modal.style.display = "none";
            }
        });
    });
});