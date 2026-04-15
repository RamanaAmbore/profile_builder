// Reveal on scroll
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.12, rootMargin: '0px 0px -60px 0px' });

document.querySelectorAll('.reveal').forEach((el) => revealObserver.observe(el));

// Active section highlighting in top nav
const navLinks = document.querySelectorAll('.nav-link');
const sectionMap = new Map();
navLinks.forEach((link) => {
  const id = link.dataset.nav;
  const section = document.getElementById(id);
  if (section) sectionMap.set(section, link);
});

const navObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    const link = sectionMap.get(entry.target);
    if (!link) return;
    if (entry.isIntersecting) {
      navLinks.forEach((l) => l.classList.remove('active'));
      link.classList.add('active');
    }
  });
}, { rootMargin: '-40% 0px -55% 0px' });

sectionMap.forEach((_, section) => navObserver.observe(section));
