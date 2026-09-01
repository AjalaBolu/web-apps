/**
 * script.js — Mental Health Support System
 * ==========================================
 * Client-side interactivity: alerts, mood chart,
 * chat auto-scroll, form validation, animations.
 */

document.addEventListener('DOMContentLoaded', () => {

  // ── Auto-dismiss flash alerts ──────────────────────────────────
  document.querySelectorAll('.alert').forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-10px)';
      alert.style.transition = 'all 0.4s ease';
      setTimeout(() => alert.remove(), 400);
    }, 4000);
  });

  // ── Mood Chart (Chart.js) ──────────────────────────────────────
  const moodCanvas = document.getElementById('moodChart');
  if (moodCanvas) {
    const labels = JSON.parse(moodCanvas.dataset.labels || '[]');
    const scores = JSON.parse(moodCanvas.dataset.scores || '[]');

    new Chart(moodCanvas, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Mood Score',
          data: scores,
          borderColor: '#d4af37',
          backgroundColor: 'rgba(212,175,55,0.08)',
          borderWidth: 2,
          pointBackgroundColor: '#d4af37',
          pointBorderColor: '#0a0a0a',
          pointBorderWidth: 2,
          pointRadius: 5,
          tension: 0.4,
          fill: true
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: '#161616',
            borderColor: 'rgba(212,175,55,0.3)',
            borderWidth: 1,
            titleColor: '#d4af37',
            bodyColor: '#aaaaaa',
            callbacks: {
              label: ctx => {
                const moods = ['','Terrible','Sad','Okay','Good','Excellent'];
                return ` ${moods[ctx.raw] || ctx.raw}  (${ctx.raw}/5)`;
              }
            }
          }
        },
        scales: {
          y: {
            min: 1, max: 5,
            ticks: {
              color: '#aaaaaa',
              stepSize: 1,
              callback: v => ['','😞','😢','😐','😊','😄'][v] || v
            },
            grid: { color: 'rgba(255,255,255,0.05)' }
          },
          x: {
            ticks: { color: '#aaaaaa', maxRotation: 30 },
            grid: { color: 'rgba(255,255,255,0.05)' }
          }
        }
      }
    });
  }

  // ── Chat auto-scroll ───────────────────────────────────────────
  const chatMessages = document.querySelector('.chat-messages');
  if (chatMessages) {
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  // ── Mood radio visual feedback ─────────────────────────────────
  document.querySelectorAll('.mood-option input[type="radio"]').forEach(radio => {
    radio.addEventListener('change', () => {
      document.querySelectorAll('.mood-btn').forEach(btn => {
        btn.style.borderColor = '';
        btn.style.background  = '';
      });
      if (radio.checked) {
        const btn = radio.nextElementSibling;
        btn.style.borderColor = '#d4af37';
        btn.style.background  = 'rgba(212,175,55,0.15)';
      }
    });
  });

  // ── Confirm destructive actions ────────────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(el => {
    el.addEventListener('click', e => {
      if (!confirm(el.dataset.confirm)) e.preventDefault();
    });
  });

  // ── Animate elements on scroll (IntersectionObserver) ──────────
  const observer = new IntersectionObserver(
    entries => entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    }),
    { threshold: 0.15 }
  );

  document.querySelectorAll('.animate-on-scroll').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(24px)';
    el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    observer.observe(el);
  });

  document.querySelectorAll('.animate-on-scroll.visible').forEach(el => {
    el.style.opacity = '1';
    el.style.transform = 'translateY(0)';
  });

  // CSS trick for observer
  const style = document.createElement('style');
  style.textContent = '.animate-on-scroll.visible { opacity: 1 !important; transform: translateY(0) !important; }';
  document.head.appendChild(style);

  // ── Sidebar active link ────────────────────────────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll('.sidebar-menu a').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

  // ── Password strength indicator ────────────────────────────────
  const pwInput = document.getElementById('password');
  const pwStrength = document.getElementById('password-strength');
  if (pwInput && pwStrength) {
    pwInput.addEventListener('input', () => {
      const val = pwInput.value;
      let score = 0;
      if (val.length >= 8)            score++;
      if (/[A-Z]/.test(val))         score++;
      if (/[0-9]/.test(val))         score++;
      if (/[^A-Za-z0-9]/.test(val))  score++;

      const levels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
      const colors = ['', '#e05252', '#d4af37', '#4a90d9', '#4caf7a'];
      pwStrength.textContent = levels[score] || '';
      pwStrength.style.color = colors[score] || '';
    });
  }

  // ── Appointment date: disable past dates ───────────────────────
  const dateInput = document.getElementById('appointment_date');
  if (dateInput) {
    const today = new Date().toISOString().split('T')[0];
    dateInput.setAttribute('min', today);
  }

  // ── Navbar scroll effect ───────────────────────────────────────
  const navbar = document.querySelector('.navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 50) {
        navbar.style.boxShadow = '0 4px 30px rgba(0,0,0,0.8)';
      } else {
        navbar.style.boxShadow = 'none';
      }
    });
  }

  // ── Message new-contact modal ──────────────────────────────────
  const startChatBtn = document.getElementById('startNewChat');
  if (startChatBtn) {
    startChatBtn.addEventListener('click', () => {
      const modal = new bootstrap.Modal(document.getElementById('newChatModal'));
      modal.show();
    });
  }

});
