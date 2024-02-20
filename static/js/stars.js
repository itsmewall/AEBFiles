// ESTRELAS

document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector('.stars-container');
    const starsCount = 800; // Número de estrelas

    for (let i = 0; i < starsCount; i++) {
      let star = document.createElement('div');
      star.className = 'star';
      star.style.left = `${Math.random() * 100}%`;
      star.style.top = `${Math.random() * 100}%`;
      star.style.animationDuration = `${Math.random() * 3 + 1}s`; // Duração da animação entre 1s e 4s
      star.style.animationDelay = `${Math.random() * 2}s`; // Delay da animação para começar em tempos diferentes

      container.appendChild(star);
    }
  });