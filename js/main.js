/**
 * AllThings Automated — Main JS
 * Handles: sticky nav, mobile menu, scroll animations,
 *          counter animations, portfolio filter, FAQ accordion,
 *          contact form validation.
 */

(function () {
  'use strict';

  /* ============================================================
     STICKY HEADER
     ============================================================ */
  const header = document.getElementById('header');
  if (header) {
    const onScroll = () => {
      header.classList.toggle('scrolled', window.scrollY > 20);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ============================================================
     MOBILE NAVIGATION TOGGLE
     ============================================================ */
  const navToggle = document.getElementById('navToggle');
  const navMenu   = document.getElementById('navMenu');

  if (navToggle && navMenu) {
    navToggle.addEventListener('click', () => {
      const isOpen = navMenu.classList.toggle('open');
      navToggle.setAttribute('aria-expanded', isOpen);

      // Animate hamburger → X
      const spans = navToggle.querySelectorAll('span');
      if (isOpen) {
        spans[0].style.cssText = 'transform:rotate(45deg) translate(5px,5px)';
        spans[1].style.cssText = 'opacity:0';
        spans[2].style.cssText = 'transform:rotate(-45deg) translate(5px,-5px)';
      } else {
        spans.forEach(s => (s.style.cssText = ''));
      }
    });

    // Close on link click
    navMenu.querySelectorAll('.nav__link').forEach(link => {
      link.addEventListener('click', () => {
        navMenu.classList.remove('open');
        navToggle.querySelectorAll('span').forEach(s => (s.style.cssText = ''));
      });
    });

    // Close on outside click
    document.addEventListener('click', e => {
      if (!header.contains(e.target)) {
        navMenu.classList.remove('open');
        navToggle.querySelectorAll('span').forEach(s => (s.style.cssText = ''));
      }
    });
  }

  /* ============================================================
     SCROLL-TRIGGERED ANIMATIONS (lightweight AOS replacement)
     ============================================================ */
  const animatedEls = document.querySelectorAll('[data-aos]');

  if (animatedEls.length) {
    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const delay = parseInt(entry.target.dataset.aosDelay || '0', 10);
            setTimeout(() => entry.target.classList.add('aos-animate'), delay);
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' }
    );

    animatedEls.forEach(el => observer.observe(el));
  }

  /* ============================================================
     ANIMATED COUNTERS
     ============================================================ */
  const counters = document.querySelectorAll('.stat__number[data-target]');

  if (counters.length) {
    const easeOut = t => 1 - Math.pow(1 - t, 3);

    const animateCounter = (el, target, duration) => {
      const start = performance.now();
      const step = now => {
        const elapsed = now - start;
        const progress = Math.min(elapsed / duration, 1);
        el.textContent = Math.round(easeOut(progress) * target);
        if (progress < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };

    const counterObserver = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const el     = entry.target;
            const target = parseInt(el.dataset.target, 10);
            animateCounter(el, target, 1800);
            counterObserver.unobserve(el);
          }
        });
      },
      { threshold: 0.5 }
    );

    counters.forEach(c => counterObserver.observe(c));
  }

  /* ============================================================
     PORTFOLIO FILTER
     ============================================================ */
  const filterContainer = document.getElementById('portfolioFilter');
  const portfolioGrid   = document.getElementById('portfolioGrid');

  if (filterContainer && portfolioGrid) {
    const cards = portfolioGrid.querySelectorAll('.portfolio-card');

    filterContainer.addEventListener('click', e => {
      const btn = e.target.closest('.filter-btn');
      if (!btn) return;

      // Update active state
      filterContainer.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      const filter = btn.dataset.filter;

      cards.forEach(card => {
        const category = card.dataset.category;
        const show     = filter === 'all' || category === filter;

        if (show) {
          card.classList.remove('hidden');
          card.style.animation = 'fadeInUp 0.4s ease forwards';
        } else {
          card.classList.add('hidden');
        }
      });
    });
  }

  /* ============================================================
     FAQ ACCORDION
     ============================================================ */
  const faqItems = document.querySelectorAll('.faq-item');

  faqItems.forEach(item => {
    const question = item.querySelector('.faq-question');
    const answer   = item.querySelector('.faq-answer');
    if (!question || !answer) return;

    question.addEventListener('click', () => {
      const isOpen = question.getAttribute('aria-expanded') === 'true';

      // Close all others
      faqItems.forEach(other => {
        if (other !== item) {
          const otherQ = other.querySelector('.faq-question');
          const otherA = other.querySelector('.faq-answer');
          if (otherQ) otherQ.setAttribute('aria-expanded', 'false');
          if (otherA) otherA.classList.remove('open');
        }
      });

      // Toggle current
      question.setAttribute('aria-expanded', !isOpen);
      answer.classList.toggle('open', !isOpen);
    });
  });

  /* ============================================================
     CONTACT FORM VALIDATION
     ============================================================ */
  const contactForm = document.getElementById('contactForm');
  const formSuccess = document.getElementById('formSuccess');
  const submitBtn   = document.getElementById('submitBtn');

  if (contactForm) {
    const showError = (id, msg) => {
      const el = document.getElementById(id);
      if (el) el.textContent = msg;
    };
    const clearErrors = () => {
      document.querySelectorAll('.form-error').forEach(el => (el.textContent = ''));
      document.querySelectorAll('.form-group input, .form-group select, .form-group textarea')
        .forEach(el => el.style.borderColor = '');
    };

    const markError = (inputId, errorId, msg) => {
      showError(errorId, msg);
      const input = document.getElementById(inputId);
      if (input) input.style.borderColor = 'var(--clr-danger)';
    };

    const validateEmail = email => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

    contactForm.addEventListener('submit', e => {
      e.preventDefault();
      clearErrors();

      let valid = true;

      const firstName   = document.getElementById('firstName');
      const lastName    = document.getElementById('lastName');
      const email       = document.getElementById('email');
      const serviceType = document.getElementById('serviceType');
      const message     = document.getElementById('message');
      const consent     = document.getElementById('consent');

      if (!firstName?.value.trim()) {
        markError('firstName', 'firstNameError', 'Please enter your first name.');
        valid = false;
      }
      if (!lastName?.value.trim()) {
        markError('lastName', 'lastNameError', 'Please enter your last name.');
        valid = false;
      }
      if (!email?.value.trim() || !validateEmail(email.value.trim())) {
        markError('email', 'emailError', 'Please enter a valid email address.');
        valid = false;
      }
      if (!serviceType?.value) {
        markError('serviceType', 'serviceTypeError', 'Please select a service.');
        valid = false;
      }
      if (!message?.value.trim() || message.value.trim().length < 10) {
        markError('message', 'messageError', 'Please tell us a bit more about your project (min 10 characters).');
        valid = false;
      }
      if (!consent?.checked) {
        showError('consentError', 'You must agree to our privacy policy to submit.');
        valid = false;
      }

      if (!valid) return;

      // Simulate form submission
      submitBtn.textContent = 'Sending…';
      submitBtn.disabled = true;

      setTimeout(() => {
        contactForm.querySelectorAll('.form-group:not(.form-group--checkbox), .form-row')
          .forEach(el => { if (el !== formSuccess) el.style.display = 'none'; });
        submitBtn.style.display = 'none';
        if (formSuccess) formSuccess.style.display = 'flex';
      }, 1200);
    });

    // Live validation: clear error on input
    contactForm.querySelectorAll('input, select, textarea').forEach(field => {
      field.addEventListener('input', () => {
        field.style.borderColor = '';
        const errorId = field.id + 'Error';
        showError(errorId, '');
      });
    });
  }

  /* ============================================================
     SMOOTH SCROLL FOR ANCHOR LINKS
     ============================================================ */
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', e => {
      const target = document.querySelector(anchor.getAttribute('href'));
      if (!target) return;
      e.preventDefault();
      const offset = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--nav-h') || '72', 10);
      const top    = target.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top, behavior: 'smooth' });
    });
  });

  /* ============================================================
     FADEUP KEYFRAME (injected for portfolio filter)
     ============================================================ */
  const style = document.createElement('style');
  style.textContent = `
    @keyframes fadeInUp {
      from { opacity: 0; transform: translateY(20px); }
      to   { opacity: 1; transform: translateY(0); }
    }
  `;
  document.head.appendChild(style);

})();
