document.addEventListener("DOMContentLoaded", () => {
  // Public-site mobile nav
  const burger = document.querySelector(".hamburger");
  const navLinks = document.querySelector(".nav__links");
  if (burger && navLinks) {
    burger.addEventListener("click", () => {
      const isOpen = navLinks.style.display === "flex";
      navLinks.style.display = isOpen ? "none" : "flex";
      navLinks.style.flexDirection = "column";
      navLinks.style.position = "absolute";
      navLinks.style.top = "100%";
      navLinks.style.left = "0";
      navLinks.style.right = "0";
      navLinks.style.background = "#fff";
      navLinks.style.padding = "16px 24px";
      navLinks.style.borderBottom = "1px solid var(--line)";
    });
  }

  // Dashboard sidebar toggle (mobile)
  const sidebarToggle = document.getElementById("sidebarToggle");
  const appSidebar = document.getElementById("appSidebar");
  if (sidebarToggle && appSidebar) {
    sidebarToggle.addEventListener("click", () => {
      appSidebar.classList.toggle("open");
    });
    document.addEventListener("click", (e) => {
      if (
        appSidebar.classList.contains("open") &&
        !appSidebar.contains(e.target) &&
        !sidebarToggle.contains(e.target)
      ) {
        appSidebar.classList.remove("open");
      }
    });
  }

  // Auto-dismiss toast alerts after 5s
  document.querySelectorAll(".toast").forEach((el) => {
    setTimeout(() => {
      el.style.transition = "opacity .4s, transform .4s";
      el.style.opacity = "0";
      el.style.transform = "translateY(-6px)";
      setTimeout(() => el.remove(), 400);
    }, 5000);
  });
});

// ===== Animated theme: scroll-reveal + count-up numbers =====
document.addEventListener("DOMContentLoaded", () => {
  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (prefersReducedMotion) return;

  // Scroll-reveal for anything marked [data-reveal]
  const revealTargets = document.querySelectorAll("[data-reveal]");
  if (revealTargets.length && "IntersectionObserver" in window) {
    const revealObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          revealObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15, rootMargin: "0px 0px -40px 0px" });
    revealTargets.forEach((el) => revealObserver.observe(el));
  }

  // Count-up animation for numbers marked [data-count-to]
  const countTargets = document.querySelectorAll("[data-count-to]");
  if (countTargets.length && "IntersectionObserver" in window) {
    const animateCount = (el) => {
      const end = parseFloat(el.getAttribute("data-count-to"));
      const suffix = el.getAttribute("data-count-suffix") || "";
      const prefix = el.getAttribute("data-count-prefix") || "";
      const decimals = el.getAttribute("data-count-decimals") ? parseInt(el.getAttribute("data-count-decimals")) : 0;
      const duration = 1400;
      const start = performance.now();

      function tick(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3); // ease-out-cubic
        const current = end * eased;
        el.textContent = prefix + current.toLocaleString(undefined, {
          minimumFractionDigits: decimals, maximumFractionDigits: decimals,
        }) + suffix;
        if (progress < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    };

    const countObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          animateCount(entry.target);
          countObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.4 });
    countTargets.forEach((el) => countObserver.observe(el));
  }
});

// ===== CV Builder — photo slot: show chosen filename + instant local preview =====
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".cv-photo-slot__input").forEach((input) => {
    input.addEventListener("change", () => {
      const file = input.files && input.files[0];
      const filenameTarget = input.dataset.filenameTarget && document.getElementById(input.dataset.filenameTarget);
      if (!file) return;

      if (filenameTarget) filenameTarget.textContent = file.name;

      // Only images can be previewed inline; a chosen PDF just shows its filename above.
      if (file.type.startsWith("image/")) {
        const frame = input.closest(".cv-photo-slot__frame");
        let img = frame.querySelector("img");
        if (!img) {
          img = document.createElement("img");
          const placeholder = frame.querySelector(".cv-photo-slot__placeholder");
          if (placeholder) placeholder.remove();
          frame.insertBefore(img, frame.querySelector(".cv-photo-slot__input"));
        }
        img.src = URL.createObjectURL(file);
        img.alt = file.name;
      }
    });
  });
});
