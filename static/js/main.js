// Bitetech Technologies - Ultra-Premium Interactive Script

document.addEventListener('DOMContentLoaded', () => {
  // Sticky navbar shadow on scroll
  const navbar = document.querySelector('.site-navbar');
  if (navbar) {
    window.addEventListener('scroll', () => {
      if (window.scrollY > 20) {
        navbar.classList.add('scrolled');
      } else {
        navbar.classList.remove('scrolled');
      }
    });
  }

  // Safe smooth scroll for in-page anchors (only for elements without bootstrap toggles)
  document.querySelectorAll('a[href^="#"]:not([data-bs-toggle]):not([data-bs-target])').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      const targetId = this.getAttribute('href');
      if (targetId && targetId !== '#' && targetId.length > 1) {
        try {
          const targetElement = document.querySelector(targetId);
          if (targetElement) {
            e.preventDefault();
            targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
          }
        } catch (err) {}
      }
    });
  });

  // =========================================================================
  // UNIVERSAL TAB SWITCHER (Customer Dashboard & In-Page Tabs)
  // =========================================================================
  document.addEventListener('click', (e) => {
    const tabBtn = e.target.closest('[data-bs-toggle="tab"]');
    if (!tabBtn) return;
    e.preventDefault();

    // 1. If Bootstrap Tab API is available, invoke it
    if (typeof bootstrap !== 'undefined' && bootstrap.Tab) {
      try {
        const bsTab = bootstrap.Tab.getOrCreateInstance(tabBtn);
        bsTab.show();
      } catch (err) {}
    }

    // 2. Direct DOM Activation Fallback
    const targetSelector = tabBtn.getAttribute('data-bs-target') || tabBtn.getAttribute('href');
    if (!targetSelector) return;

    // Deactivate siblings in the tab list
    const navList = tabBtn.closest('.nav, ul');
    if (navList) {
      navList.querySelectorAll('.nav-link, button').forEach(btn => {
        btn.classList.remove('active');
        btn.setAttribute('aria-selected', 'false');
      });
    }
    tabBtn.classList.add('active');
    tabBtn.setAttribute('aria-selected', 'true');

    // Show corresponding tab pane
    try {
      const targetPane = document.querySelector(targetSelector);
      if (targetPane) {
        const tabContent = targetPane.closest('.tab-content') || targetPane.parentElement;
        if (tabContent) {
          tabContent.querySelectorAll('.tab-pane').forEach(pane => {
            pane.classList.remove('show', 'active');
          });
        }
        targetPane.classList.add('show', 'active');
      }
    } catch (err) {}
  });

  // Activate tab from URL hash on page load
  if (window.location.hash) {
    try {
      const hashTabBtn = document.querySelector(`[data-bs-target="${window.location.hash}"], [href="${window.location.hash}"]`);
      if (hashTabBtn) {
        setTimeout(() => hashTabBtn.click(), 50);
      }
    } catch (err) {}
  }


  // =========================================================================
  // UNIVERSAL OFFCANVAS TOGGLE (3-Dash Hamburger Menu)
  // =========================================================================
  document.addEventListener('click', (e) => {
    const toggleBtn = e.target.closest('[data-bs-toggle="offcanvas"]');
    if (toggleBtn) {
      e.preventDefault();
      const targetSelector = toggleBtn.getAttribute('data-bs-target') || toggleBtn.getAttribute('href');
      const offcanvasEl = targetSelector ? document.querySelector(targetSelector) : null;
      if (offcanvasEl) {
        if (typeof bootstrap !== 'undefined' && bootstrap.Offcanvas) {
          try {
            bootstrap.Offcanvas.getOrCreateInstance(offcanvasEl).toggle();
            return;
          } catch (err) {}
        }
        offcanvasEl.classList.toggle('show');
        if (offcanvasEl.classList.contains('show')) {
          let backdrop = document.querySelector('.offcanvas-backdrop');
          if (!backdrop) {
            backdrop = document.createElement('div');
            backdrop.className = 'offcanvas-backdrop fade show';
            document.body.appendChild(backdrop);
            backdrop.addEventListener('click', () => {
              offcanvasEl.classList.remove('show');
              backdrop.remove();
            });
          }
        } else {
          const backdrop = document.querySelector('.offcanvas-backdrop');
          if (backdrop) backdrop.remove();
        }
      }
      return;
    }

    const dismissBtn = e.target.closest('[data-bs-dismiss="offcanvas"]');
    if (dismissBtn) {
      e.preventDefault();
      const offcanvasEl = dismissBtn.closest('.offcanvas');
      if (offcanvasEl) {
        if (typeof bootstrap !== 'undefined' && bootstrap.Offcanvas) {
          try {
            bootstrap.Offcanvas.getOrCreateInstance(offcanvasEl).hide();
            return;
          } catch (err) {}
        }
        offcanvasEl.classList.remove('show');
        const backdrop = document.querySelector('.offcanvas-backdrop');
        if (backdrop) backdrop.remove();
      }
    }
  });

  // =========================================================================
  // UNIVERSAL DROPDOWNS (User Account Dropdown)
  // =========================================================================
  document.addEventListener('click', (e) => {
    const dropdownToggle = e.target.closest('[data-bs-toggle="dropdown"]');
    if (dropdownToggle) {
      e.preventDefault();
      if (typeof bootstrap !== 'undefined' && bootstrap.Dropdown) {
        try {
          bootstrap.Dropdown.getOrCreateInstance(dropdownToggle).toggle();
          return;
        } catch (err) {}
      }
      const parent = dropdownToggle.closest('.dropdown');
      const menu = parent ? parent.querySelector('.dropdown-menu') : null;
      if (menu) {
        const isShown = menu.classList.contains('show');
        document.querySelectorAll('.dropdown-menu.show').forEach(m => m.classList.remove('show'));
        if (!isShown) menu.classList.add('show');
      }
      return;
    }

    // Click outside closes open dropdowns
    if (!e.target.closest('.dropdown')) {
      document.querySelectorAll('.dropdown-menu.show').forEach(m => m.classList.remove('show'));
    }
  });

  // Client-side quick filter for projects page
  const searchInput = document.getElementById('projectSearchInput');
  const projectCards = document.querySelectorAll('.project-card-item');

  if (searchInput && projectCards.length > 0) {
    searchInput.addEventListener('input', (e) => {
      const term = e.target.value.toLowerCase().trim();
      projectCards.forEach(card => {
        const title = card.getAttribute('data-title') || '';
        const tech = card.getAttribute('data-tech') || '';
        const desc = card.getAttribute('data-desc') || '';
        const combined = `${title} ${tech} ${desc}`.toLowerCase();

        if (term === '' || combined.includes(term)) {
          card.style.display = '';
        } else {
          card.style.display = 'none';
        }
      });
    });
  }

  // Auto-dismiss alert banners after 6 seconds
  const autoAlerts = document.querySelectorAll('.alert-dismissible');
  autoAlerts.forEach(alert => {
    setTimeout(() => {
      try {
        const bsAlert = new bootstrap.Alert(alert);
        bsAlert.close();
      } catch (err) {
        alert.remove();
      }
    }, 6000);
  });

  // =========================================================================
  // CREATIVE FLOATING CONTACT HUB SPEED-DIAL
  // =========================================================================
  const contactHub = document.getElementById('contactHub');
  const contactHubToggle = document.getElementById('contactHubToggle');
  const closeContactHub = document.getElementById('closeContactHub');

  if (contactHub && contactHubToggle) {
    contactHubToggle.addEventListener('click', (e) => {
      e.stopPropagation();
      contactHub.classList.toggle('active');
    });

    if (closeContactHub) {
      closeContactHub.addEventListener('click', (e) => {
        e.stopPropagation();
        contactHub.classList.remove('active');
      });
    }

    // Close when clicking anywhere outside
    document.addEventListener('click', (e) => {
      if (!contactHub.contains(e.target)) {
        contactHub.classList.remove('active');
      }
    });
  }

  // =========================================================================
  // CREATIVE INSTANT PROJECT ESTIMATOR / 1-CLICK WHATSAPP CALCULATOR
  // =========================================================================
  const estimatorPills = document.querySelectorAll('.estimator-pill-btn');
  const estimatorPrice = document.getElementById('estimatorPrice');
  const estimatorTimeline = document.getElementById('estimatorTimeline');
  const estimatorDesc = document.getElementById('estimatorDesc');
  const estimatorBadge = document.getElementById('estimatorBadge');
  const estimatorWaBtn = document.getElementById('estimatorWaBtn');
  const estimatorFormBtn = document.getElementById('estimatorFormBtn');
  const estimatorFeaturesList = document.getElementById('estimatorFeaturesList');

  const estimatorData = {
    'mini': {
      title: 'Python Mini Project',
      price: '₹599',
      badge: 'Academic Mini Project',
      timeline: 'Delivered in 24 Hours',
      desc: 'Ideal for college semester submissions, lab examinations, and practical viva demonstrations. Delivered with clean source code and setup guide.',
      features: [
        'Complete bug-free Python source code (GUI/Tkinter or CLI)',
        'Pre-recorded video demonstration showing working output',
        'Step-by-step installation instructions & dependency guide',
        'Academic Viva Voce Q&A cheat sheet included'
      ],
      waMessage: 'Hello Bitetech Technologies, I would like to order a Python Mini Project starting at ₹599. Please share available topics.',
      serviceId: 'mini-project'
    },
    'major': {
      title: 'Python Major Project',
      price: '₹1,000',
      badge: 'Full-Stack Engineering',
      timeline: 'Delivered in 2 to 3 Days',
      desc: 'Comprehensive full-stack Python application utilizing Flask/Django, MySQL/SQLite database schema, authentication, and full presentation deliverables.',
      features: [
        'Full-stack architecture with relational database schema & models',
        'Admin dashboard, user authentication, and CRUD business logic',
        'Complete Project Synopsis, System Architecture diagram & Report',
        'Free remote setup assistance via AnyDesk/TeamViewer'
      ],
      waMessage: 'Hello Bitetech Technologies, I would like to discuss a Python Major Project starting at ₹1,000. Here are my requirements:',
      serviceId: 'major-project'
    },
    'website': {
      title: 'Shop or Small Business Website',
      price: '₹5,000',
      badge: 'Professional Commercial Web',
      timeline: 'Delivered in 5 to 7 Days',
      desc: 'High-converting responsive business website designed for retail shops, clinics, consultants, and startups with WhatsApp lead capture.',
      features: [
        'Up to 5 custom-designed mobile-responsive pages',
        'Instant WhatsApp chat integration & lead capture forms',
        'Google Maps business location & catalog showcase',
        'Fast page loading speed and SEO optimization baseline'
      ],
      waMessage: 'Hello Bitetech Technologies, I need a Business Website starting at ₹5,000. Can we schedule a quick consultation?',
      serviceId: 'website'
    },
    'hosting': {
      title: 'Business Website with 1-Year Hosting',
      price: '₹7,000',
      badge: 'All-Inclusive Live Launch',
      timeline: 'Delivered in 7 Days',
      desc: 'Turnkey online deployment. We design your website and deploy it live with custom domain linkage, free SSL encryption, and high-speed cloud hosting.',
      features: [
        'Complete 5-page custom responsive website',
        '1-Year Cloud Hosting with 99.9% uptime guarantee',
        'Free SSL Security Certificate & Custom Domain configuration',
        '1 Year of technical maintenance and support'
      ],
      waMessage: 'Hello Bitetech Technologies, I want the Complete Website + Hosting package at ₹7,000. Please let me know how to start.',
      serviceId: 'website-hosting'
    }
  };

  if (estimatorPills.length > 0 && estimatorPrice && estimatorWaBtn) {
    const companyPhone = estimatorWaBtn.getAttribute('data-phone') || '7418332912';

    estimatorPills.forEach(pill => {
      pill.addEventListener('click', () => {
        estimatorPills.forEach(p => p.classList.remove('active'));
        pill.classList.add('active');

        const key = pill.getAttribute('data-type');
        const data = estimatorData[key];
        if (!data) return;

        // Smooth transition
        estimatorPrice.textContent = data.price;
        if (estimatorTimeline) estimatorTimeline.textContent = data.timeline;
        if (estimatorDesc) estimatorDesc.textContent = data.desc;
        if (estimatorBadge) estimatorBadge.textContent = data.badge;

        // Update features list
        if (estimatorFeaturesList) {
          estimatorFeaturesList.innerHTML = data.features.map(f => 
            `<li><i class="bi bi-check2-circle text-emerald me-2"></i> ${f}</li>`
          ).join('');
        }

        // Update WhatsApp link
        const encodedMsg = encodeURIComponent(data.waMessage);
        estimatorWaBtn.href = `https://wa.me/91${companyPhone}?text=${encodedMsg}`;

        // Update Form scroll
        if (estimatorFormBtn) {
          estimatorFormBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const contactSection = document.getElementById('contact-section');
            if (contactSection) {
              contactSection.scrollIntoView({ behavior: 'smooth' });
              const subjectInput = document.querySelector('input[name="subject"]');
              if (subjectInput) {
                subjectInput.value = `Inquiry regarding ${data.title} (${data.price})`;
              }
            }
          });
        }
      });
    });
  }
});
