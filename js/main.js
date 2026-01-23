// Debounce function for performance optimization
function debounce(func, wait) {
    var timeout;
    return function() {
        var context = this, args = arguments;
        clearTimeout(timeout);
        timeout = setTimeout(function() {
            func.apply(context, args);
        }, wait);
    };
}

// Reusable toggle function
function toggleClasses(triggerElement, targetElement, class1, class2) {
    $(triggerElement).click(function () {
        var $target = $(targetElement);
        if ($target.hasClass(class1)) {
            $target.removeClass(class1).addClass(class2);
        } else {
            $target.removeClass(class2).addClass(class1);
        }
    });
}

// Resize handling
function initResizeHandler() {
    var $window = $(window);
    var $page = $(".page");
    var $sideCard = $(".side-card");

    var handleResize = function () {
        if ($window.width() < 1280 && $window.width() > 540) {
            $page.css({
                "width": $window.width() - $sideCard.width() - 90,
                "float": "left"
            });
        } else {
            $page.removeAttr("style");
        }
    };

    // Use debounce to improve performance
    $window.resize(debounce(handleResize, 250));
    // Run once on init
    handleResize();
}

// Menu interactions
function initMenuHandlers() {
    // Initialize toggle handlers
    toggleClasses(".menus_icon", ".header_wrap", "menus-open", "menus-close");
    toggleClasses(".m-social-links", ".author-links", "is-open", "is-close");
    toggleClasses(".site-nav", ".nav", "nav-open", "nav-close");

    // Click outside handler
    $(document).click(function(e){
        var target = $(e.target);

        // Close navigation if clicking outside
        if(target.closest(".nav").length === 0) {
            $(".nav").removeClass("nav-open").addClass("nav-close");
        }

        // Close social links if clicking outside
        if(target.closest(".author-links").length === 0) {
            $(".author-links").removeClass("is-open").addClass("is-close");
        }

        // Close menu if clicking outside
        if(target.closest(".menus_icon").length === 0 && target.closest(".menus_items").length === 0) {
            $(".header_wrap").removeClass("menus-open").addClass("menus-close");
        }
    });
}

// Back to top functionality
function initBackToTop() {
    var offset = 100,
        scroll_top_duration = 700,
        $back_to_top = $('.nav-wrap');

    // Hide or show the "back to top" link
    $(window).scroll(function () {
        ($(this).scrollTop() > offset) ? $back_to_top.addClass('is-visible') : $back_to_top.removeClass('is-visible');
    });

    // Smooth scroll to top
    $('.cd-top').on('click', function (event) {
        event.preventDefault();
        $('body,html').animate({
            scrollTop: 0,
        }, scroll_top_duration);
    });
}

// Pjax initialization
function initPjax() {
    $(document).pjax('a[target!=_blank]','.page', {
        fragment: '.page',
        timeout: 5000
    });
    $(document).on({
        'pjax:click': function() {
            $('body,html').animate({
                scrollTop: 0,
            }, 700);
        },
        'pjax:end': function() {
            // Reset all menu states
            resetMenuStates();
        }
    });
}

// Smooth scroll initialization
function initSmoothScroll() {
    $('a[href*=\#]:not([href=\#])').click(function () {
        if (location.pathname.replace(/^\//, '') === this.pathname.replace(/^\//, '') && location.hostname === this.hostname) {
            var target = $(this.hash);
            target = target.length ? target : $('[name=' + this.hash.slice(1) + ']');
            if (target.length) {
                $('html,body').animate({
                    scrollTop: target.offset().top
                }, 700);
                return false;
            }
        }
    });
}

// Reset all menu states
function resetMenuStates() {
    if ($('.header_wrap').hasClass('menus-open')) {
        $('.header_wrap').removeClass('menus-open').addClass('menus-close');
    }
    if ($('.author-links').hasClass('is-open')) {
        $('.author-links').removeClass('is-open').addClass('is-close');
    }
    if ($('.nav').hasClass('nav-open')) {
        $('.nav').removeClass('nav-open').addClass('nav-close');
    }
}

// Initialize all functionality
$(function () {
    initResizeHandler();
    initMenuHandlers();
    initBackToTop();
    initPjax();
    initSmoothScroll();
});