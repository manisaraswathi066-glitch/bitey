// Bitetech Technologies - Ultra-Reliable Admin Scripts

document.addEventListener('DOMContentLoaded', () => {
  // Mobile sidebar toggle with overlay backdrop
  const sidebarToggler = document.getElementById('adminSidebarToggle');
  const sidebar = document.querySelector('.admin-sidebar');
  
  if (sidebarToggler && sidebar) {
    sidebarToggler.addEventListener('click', (e) => {
      e.stopPropagation();
      sidebar.classList.toggle('show');
      
      let backdrop = document.querySelector('.admin-sidebar-backdrop');
      if (sidebar.classList.contains('show')) {
        if (!backdrop) {
          backdrop = document.createElement('div');
          backdrop.className = 'admin-sidebar-backdrop';
          backdrop.style.cssText = 'position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,0.6);z-index:1020;backdrop-filter:blur(3px);';
          document.body.appendChild(backdrop);
          backdrop.addEventListener('click', () => {
            sidebar.classList.remove('show');
            backdrop.remove();
          });
        }
      } else if (backdrop) {
        backdrop.remove();
      }
    });

    // Close sidebar on window resize to desktop
    window.addEventListener('resize', () => {
      if (window.innerWidth > 992) {
        sidebar.classList.remove('show');
        const backdrop = document.querySelector('.admin-sidebar-backdrop');
        if (backdrop) backdrop.remove();
      }
    });
  }

  // Universal Modal Controller (Update Status modals in enquiries, etc.)
  document.addEventListener('click', (e) => {
    // 1. Open Modal Trigger
    const modalBtn = e.target.closest('[data-bs-toggle="modal"]');
    if (modalBtn) {
      e.preventDefault();
      const targetSelector = modalBtn.getAttribute('data-bs-target') || modalBtn.getAttribute('href');
      const modalEl = targetSelector ? document.querySelector(targetSelector) : null;
      if (modalEl) {
        // Try Bootstrap API first
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
          try {
            const bsModal = bootstrap.Modal.getOrCreateInstance(modalEl);
            bsModal.show();
            return;
          } catch (err) {}
        }
        // Direct DOM Fallback
        modalEl.classList.add('show');
        modalEl.style.display = 'block';
        modalEl.setAttribute('aria-modal', 'true');
        modalEl.removeAttribute('aria-hidden');
        document.body.classList.add('modal-open');

        let backdrop = document.querySelector('.modal-backdrop');
        if (!backdrop) {
          backdrop = document.createElement('div');
          backdrop.className = 'modal-backdrop fade show';
          document.body.appendChild(backdrop);
          backdrop.addEventListener('click', () => {
            modalEl.classList.remove('show');
            modalEl.style.display = 'none';
            document.body.classList.remove('modal-open');
            backdrop.remove();
          });
        }
      }
      return;
    }

    // 2. Dismiss Modal Trigger
    const dismissBtn = e.target.closest('[data-bs-dismiss="modal"]');
    if (dismissBtn) {
      e.preventDefault();
      const modalEl = dismissBtn.closest('.modal');
      if (modalEl) {
        if (typeof bootstrap !== 'undefined' && bootstrap.Modal) {
          try {
            const bsModal = bootstrap.Modal.getOrCreateInstance(modalEl);
            bsModal.hide();
            return;
          } catch (err) {}
        }
        modalEl.classList.remove('show');
        modalEl.style.display = 'none';
        modalEl.setAttribute('aria-hidden', 'true');
        document.body.classList.remove('modal-open');
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) backdrop.remove();
      }
    }
  });

  // Universal Tab Switcher (In-page tabs)
  document.addEventListener('click', (e) => {
    const tabBtn = e.target.closest('[data-bs-toggle="tab"]');
    if (!tabBtn) return;
    e.preventDefault();

    if (typeof bootstrap !== 'undefined' && bootstrap.Tab) {
      try {
        bootstrap.Tab.getOrCreateInstance(tabBtn).show();
      } catch (err) {}
    }

    const targetSelector = tabBtn.getAttribute('data-bs-target') || tabBtn.getAttribute('href');
    if (!targetSelector) return;

    const navList = tabBtn.closest('.nav, ul');
    if (navList) {
      navList.querySelectorAll('.nav-link, button').forEach(b => b.classList.remove('active'));
    }
    tabBtn.classList.add('active');

    const targetPane = document.querySelector(targetSelector);
    if (targetPane) {
      const parent = targetPane.closest('.tab-content') || targetPane.parentElement;
      if (parent) {
        parent.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('show', 'active'));
      }
      targetPane.classList.add('show', 'active');
    }
  });

  // Confirm delete forms
  document.querySelectorAll('.delete-confirm-form').forEach(form => {
    form.addEventListener('submit', (e) => {
      const entity = form.getAttribute('data-entity') || 'item';
      if (!confirm(`Are you sure you want to permanently delete this ${entity}? This action cannot be undone.`)) {
        e.preventDefault();
      }
    });
  });

  // Auto-dismiss alert banners
  document.querySelectorAll('.alert-dismissible').forEach(alert => {
    setTimeout(() => {
      try {
        if (typeof bootstrap !== 'undefined' && bootstrap.Alert) {
          new bootstrap.Alert(alert).close();
        } else {
          alert.remove();
        }
      } catch (err) {
        alert.remove();
      }
    }, 6000);
  });
});
