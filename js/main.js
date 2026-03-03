(() => {
  function debounce(func, wait) {
    let timeoutId;
    return (...args) => {
      window.clearTimeout(timeoutId);
      timeoutId = window.setTimeout(() => func(...args), wait);
    };
  }

  function toggleClasses(triggerSelector, targetSelector, class1, class2) {
    const target = document.querySelector(targetSelector);
    if (!target) return;
    document.querySelectorAll(triggerSelector).forEach((trigger) => {
      trigger.addEventListener("click", (event) => {
        event.preventDefault();
        if (target.classList.contains(class1)) {
          target.classList.remove(class1);
          target.classList.add(class2);
        } else {
          target.classList.remove(class2);
          target.classList.add(class1);
        }
      });
    });
  }

  function resetMenuStates() {
    const headerWrap = document.querySelector(".header_wrap");
    const authorLinks = document.querySelector(".author-links");
    const nav = document.querySelector(".nav");

    if (headerWrap && headerWrap.classList.contains("menus-open")) {
      headerWrap.classList.remove("menus-open");
      headerWrap.classList.add("menus-close");
    }
    if (authorLinks && authorLinks.classList.contains("is-open")) {
      authorLinks.classList.remove("is-open");
      authorLinks.classList.add("is-close");
    }
    if (nav && nav.classList.contains("nav-open")) {
      nav.classList.remove("nav-open");
      nav.classList.add("nav-close");
    }
  }

  function initResizeHandler() {
    const page = document.querySelector(".page");
    const sideCard = document.querySelector(".side-card");
    if (!page || !sideCard) return;

    const handleResize = () => {
      const width = window.innerWidth;
      if (width < 1280 && width > 540) {
        const sideCardWidth = sideCard.getBoundingClientRect().width;
        const pageWidth = Math.max(0, width - sideCardWidth - 90);
        page.style.width = `${pageWidth}px`;
        page.style.float = "left";
      } else {
        page.style.removeProperty("width");
        page.style.removeProperty("float");
      }
    };

    window.addEventListener("resize", debounce(handleResize, 250));
    handleResize();
  }

  function initMenuHandlers() {
    toggleClasses(".menus_icon", ".header_wrap", "menus-open", "menus-close");
    toggleClasses(".m-social-links", ".author-links", "is-open", "is-close");
    toggleClasses(".site-nav", ".nav", "nav-open", "nav-close");

    document.addEventListener("click", (event) => {
      const target = event.target instanceof Element ? event.target : null;
      if (!target) return;

      if (!target.closest(".nav")) {
        const nav = document.querySelector(".nav");
        if (nav) {
          nav.classList.remove("nav-open");
          nav.classList.add("nav-close");
        }
      }

      if (!target.closest(".author-links")) {
        const authorLinks = document.querySelector(".author-links");
        if (authorLinks) {
          authorLinks.classList.remove("is-open");
          authorLinks.classList.add("is-close");
        }
      }

      if (!target.closest(".menus_icon") && !target.closest(".menus_items")) {
        const headerWrap = document.querySelector(".header_wrap");
        if (headerWrap) {
          headerWrap.classList.remove("menus-open");
          headerWrap.classList.add("menus-close");
        }
      }
    });
  }

  function initBackToTop() {
    const backToTopWrap = document.querySelector(".nav-wrap");
    const backToTopButton = document.querySelector(".cd-top");
    if (!backToTopWrap || !backToTopButton) return;

    const updateVisibility = () => {
      if (window.scrollY > 100) backToTopWrap.classList.add("is-visible");
      else backToTopWrap.classList.remove("is-visible");
    };

    window.addEventListener("scroll", updateVisibility, { passive: true });
    updateVisibility();

    backToTopButton.addEventListener("click", (event) => {
      event.preventDefault();
      if ("scrollBehavior" in document.documentElement.style) {
        window.scrollTo({ top: 0, behavior: "smooth" });
      } else {
        window.scrollTo(0, 0);
      }
      resetMenuStates();
    });
  }

  function initSmoothScroll() {
    document.addEventListener("click", (event) => {
      const target = event.target instanceof Element ? event.target : null;
      const anchor = target ? target.closest("a[href]") : null;
      if (!anchor) return;

      const href = anchor.getAttribute("href");
      if (!href || href === "#" || !href.includes("#")) return;
      if (anchor.getAttribute("target") === "_blank") return;

      let url;
      try {
        url = new URL(href, window.location.href);
      } catch {
        return;
      }

      if (url.origin !== window.location.origin || url.pathname !== window.location.pathname) return;
      if (!url.hash) return;

      const id = decodeURIComponent(url.hash.slice(1));
      const scrollTarget = document.getElementById(id);
      if (!scrollTarget) return;

      event.preventDefault();
      if ("scrollBehavior" in document.documentElement.style) {
        scrollTarget.scrollIntoView({ behavior: "smooth", block: "start" });
      } else {
        scrollTarget.scrollIntoView(true);
      }
      resetMenuStates();
    });
  }

  function initImageFallbacks() {
    document.querySelectorAll("img[data-fallback-src]").forEach((img) => {
      const fallbackSrc = img.getAttribute("data-fallback-src");
      if (!fallbackSrc) return;

      const applyFallback = () => {
        img.removeEventListener("error", applyFallback);
        img.removeAttribute("data-fallback-src");
        img.src = fallbackSrc;
      };

      img.addEventListener("error", applyFallback);
      if (img.complete && img.naturalWidth === 0) applyFallback();
    });
  }

  function init() {
    initResizeHandler();
    initMenuHandlers();
    initBackToTop();
    initSmoothScroll();
    initImageFallbacks();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
