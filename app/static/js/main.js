document.addEventListener("DOMContentLoaded", () => {
  const flashElements = document.querySelectorAll(".flash");
  if (!flashElements.length) {
    return;
  }
  window.setTimeout(() => {
    flashElements.forEach((el) => {
      el.style.transition = "opacity 0.4s ease";
      el.style.opacity = "0";
      window.setTimeout(() => el.remove(), 420);
    });
  }, 6000);
});

