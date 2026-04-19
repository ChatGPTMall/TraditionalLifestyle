/**
 * TraditionalLifestyle - GSAP Animations
 * Signature animations for premium salon experience
 */

// Register GSAP plugins
gsap.registerPlugin(ScrollTrigger);

/**
 * Initialize all animations
 */
function initAnimations() {
    initNavbarAnimation();
    initHeroAnimations();
    initScrollAnimations();
    initHoverAnimations();
    initPageTransitions();
}

/**
 * Navbar scroll animation
 */
function initNavbarAnimation() {
    const navbar = document.getElementById('main-nav');
    if (!navbar) return;

    ScrollTrigger.create({
        start: 'top -80',
        onUpdate: (self) => {
            if (self.direction === 1) {
                gsap.to(navbar, {
                    y: -100,
                    duration: 0.3,
                    ease: 'power2.out'
                });
            } else {
                gsap.to(navbar, {
                    y: 0,
                    duration: 0.3,
                    ease: 'power2.out'
                });
            }
        }
    });

    // Navbar background on scroll
    ScrollTrigger.create({
        start: 'top -50',
        onEnter: () => {
            navbar.classList.add('navbar-scrolled');
            gsap.to(navbar, {
                boxShadow: '0 4px 30px rgba(0,0,0,0.1)',
                duration: 0.3
            });
        },
        onLeaveBack: () => {
            navbar.classList.remove('navbar-scrolled');
            gsap.to(navbar, {
                boxShadow: 'none',
                duration: 0.3
            });
        }
    });
}

/**
 * Hero section animations
 */
function initHeroAnimations() {
    // Hero content fade in
    const heroContent = document.querySelector('.hero-content');
    if (heroContent) {
        const heroTl = gsap.timeline({ defaults: { ease: 'power3.out' } });

        heroTl.from('.hero-subtitle, .section-subtitle', {
            opacity: 0,
            y: 30,
            duration: 0.8
        });

        heroTl.from('.hero-title, h1', {
            opacity: 0,
            y: 50,
            duration: 1,
            stagger: 0.1
        }, '-=0.4');

        heroTl.from('.hero-description, .hero-cta, .btn', {
            opacity: 0,
            y: 30,
            duration: 0.8,
            stagger: 0.2
        }, '-=0.5');
    }

    // Blade swipe reveal animation
    bladeSwipeReveal();
}

/**
 * Blade Swipe - Hero reveal animation
 */
function bladeSwipeReveal() {
    const heroElements = document.querySelectorAll('.blade-reveal');

    heroElements.forEach(element => {
        gsap.from(element, {
            clipPath: 'polygon(0 0, 0 0, 0 100%, 0 100%)',
            duration: 1.2,
            ease: 'power4.out',
            scrollTrigger: {
                trigger: element,
                start: 'top 80%',
                toggleActions: 'play none none none'
            }
        });
    });
}

/**
 * Scroll-triggered animations
 */
function initScrollAnimations() {
    // Fade up animation
    gsap.utils.toArray('.fade-up').forEach(element => {
        gsap.from(element, {
            opacity: 0,
            y: 60,
            duration: 1,
            ease: 'power3.out',
            scrollTrigger: {
                trigger: element,
                start: 'top 85%',
                toggleActions: 'play none none none'
            }
        });
    });

    // Staggered card animations
    gsap.utils.toArray('.cards-container').forEach(container => {
        const cards = container.querySelectorAll('.card, .service-card-men, .service-card-women, .staff-card-men, .staff-card-women');

        gsap.from(cards, {
            opacity: 0,
            y: 80,
            duration: 0.8,
            stagger: 0.15,
            ease: 'power3.out',
            scrollTrigger: {
                trigger: container,
                start: 'top 80%',
                toggleActions: 'play none none none'
            }
        });
    });

    // Section title animations
    gsap.utils.toArray('.section-title').forEach(title => {
        const subtitle = title.querySelector('.section-subtitle');
        const heading = title.querySelector('h2, h3');
        const line = title.querySelector('.gold-line, .rose-line');

        const tl = gsap.timeline({
            scrollTrigger: {
                trigger: title,
                start: 'top 85%',
                toggleActions: 'play none none none'
            }
        });

        if (subtitle) {
            tl.from(subtitle, { opacity: 0, y: 20, duration: 0.6 });
        }
        if (heading) {
            tl.from(heading, { opacity: 0, y: 30, duration: 0.8 }, '-=0.3');
        }
        if (line) {
            tl.from(line, { scaleX: 0, duration: 0.6 }, '-=0.4');
        }
    });

    // Parallax effect
    gsap.utils.toArray('.parallax').forEach(element => {
        gsap.to(element, {
            yPercent: -20,
            ease: 'none',
            scrollTrigger: {
                trigger: element,
                start: 'top bottom',
                end: 'bottom top',
                scrub: true
            }
        });
    });

    // Hair flow animation (scroll-triggered path animation)
    initHairFlowAnimation();

    // Counter animation
    initCounterAnimation();
}

/**
 * Hair Flow - Scroll-triggered path animation
 */
function initHairFlowAnimation() {
    const hairStrands = document.querySelectorAll('.hair-strand');
    const hairPath = document.querySelector('#hair-path');

    if (hairStrands.length && hairPath) {
        hairStrands.forEach((strand, index) => {
            gsap.to(strand, {
                motionPath: {
                    path: hairPath,
                    align: hairPath,
                    alignOrigin: [0.5, 0.5]
                },
                duration: 2 + index * 0.2,
                ease: 'power1.inOut',
                scrollTrigger: {
                    trigger: '.services-section',
                    start: 'top center',
                    toggleActions: 'play none none reverse'
                }
            });
        });
    }
}

/**
 * Counter animation for statistics
 */
function initCounterAnimation() {
    gsap.utils.toArray('.counter').forEach(counter => {
        const target = parseInt(counter.getAttribute('data-target'));

        gsap.to(counter, {
            innerHTML: target,
            duration: 2,
            ease: 'power2.out',
            snap: { innerHTML: 1 },
            scrollTrigger: {
                trigger: counter,
                start: 'top 90%',
                toggleActions: 'play none none none'
            }
        });
    });
}

/**
 * Hover animations
 */
function initHoverAnimations() {
    // Button hover effect
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('mouseenter', () => {
            gsap.to(btn, {
                scale: 1.05,
                duration: 0.3,
                ease: 'power2.out'
            });
        });

        btn.addEventListener('mouseleave', () => {
            gsap.to(btn, {
                scale: 1,
                duration: 0.3,
                ease: 'power2.out'
            });
        });
    });

    // Card hover magnetic effect
    document.querySelectorAll('.card, .service-card-men, .service-card-women').forEach(card => {
        card.addEventListener('mousemove', (e) => {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;

            gsap.to(card, {
                rotationY: x / 20,
                rotationX: -y / 20,
                duration: 0.5,
                ease: 'power2.out',
                transformPerspective: 1000
            });
        });

        card.addEventListener('mouseleave', () => {
            gsap.to(card, {
                rotationY: 0,
                rotationX: 0,
                duration: 0.5,
                ease: 'power2.out'
            });
        });
    });

    // Image zoom on hover
    document.querySelectorAll('.image-zoom').forEach(container => {
        const img = container.querySelector('img');
        if (!img) return;

        container.addEventListener('mouseenter', () => {
            gsap.to(img, {
                scale: 1.1,
                duration: 0.6,
                ease: 'power2.out'
            });
        });

        container.addEventListener('mouseleave', () => {
            gsap.to(img, {
                scale: 1,
                duration: 0.6,
                ease: 'power2.out'
            });
        });
    });
}

/**
 * Page transition animations
 */
function initPageTransitions() {
    // Scissor cut transition for internal links
    document.querySelectorAll('a[data-transition="scissor"]').forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const href = link.getAttribute('href');
            scissorCutTransition(href);
        });
    });
}

/**
 * Scissor Cut - Page transition effect
 */
function scissorCutTransition(url) {
    // Create overlay if not exists
    let overlay = document.querySelector('.scissor-transition-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.className = 'scissor-transition-overlay';
        overlay.innerHTML = `
            <svg class="scissor-svg" viewBox="0 0 100 100" style="width: 150px; height: 150px;">
                <g class="scissor-group">
                    <path class="scissor-blade scissor-blade-top" d="M50 35 L85 20 L87 25 L52 42 Z" fill="var(--color-accent)"/>
                    <path class="scissor-blade scissor-blade-bottom" d="M50 65 L85 80 L87 75 L52 58 Z" fill="var(--color-accent)"/>
                    <circle cx="30" cy="35" r="12" fill="none" stroke="var(--color-accent)" stroke-width="3"/>
                    <circle cx="30" cy="65" r="12" fill="none" stroke="var(--color-accent)" stroke-width="3"/>
                    <circle cx="50" cy="50" r="4" fill="var(--color-accent)"/>
                </g>
            </svg>
        `;
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: var(--color-bg);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            pointer-events: none;
        `;
        document.body.appendChild(overlay);
    }

    const tl = gsap.timeline({
        onComplete: () => {
            window.location.href = url;
        }
    });

    tl.to(overlay, { opacity: 1, pointerEvents: 'auto', duration: 0.3 });
    tl.to('.scissor-blade-top', { rotation: -30, transformOrigin: '50% 50%', duration: 0.2 });
    tl.to('.scissor-blade-bottom', { rotation: 30, transformOrigin: '50% 50%', duration: 0.2 }, '<');
    tl.to('.scissor-blade-top', { rotation: 0, duration: 0.15 });
    tl.to('.scissor-blade-bottom', { rotation: 0, duration: 0.15 }, '<');
    tl.to('#main-content', {
        clipPath: 'polygon(0 50%, 100% 50%, 100% 50%, 0 50%)',
        duration: 0.5,
        ease: 'power2.inOut'
    }, '-=0.2');
}

/**
 * Magnetic button effect
 */
function initMagneticButtons() {
    document.querySelectorAll('.btn-magnetic').forEach(btn => {
        btn.addEventListener('mousemove', (e) => {
            const rect = btn.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;

            gsap.to(btn, {
                x: x * 0.3,
                y: y * 0.3,
                duration: 0.3,
                ease: 'power2.out'
            });
        });

        btn.addEventListener('mouseleave', () => {
            gsap.to(btn, {
                x: 0,
                y: 0,
                duration: 0.5,
                ease: 'elastic.out(1, 0.3)'
            });
        });
    });
}

/**
 * Text reveal animation
 */
function initTextReveal() {
    gsap.utils.toArray('.text-reveal').forEach(text => {
        const chars = text.textContent.split('');
        text.innerHTML = chars.map(char =>
            char === ' ' ? ' ' : `<span class="char">${char}</span>`
        ).join('');

        gsap.from(text.querySelectorAll('.char'), {
            opacity: 0,
            y: 50,
            rotationX: -90,
            stagger: 0.02,
            duration: 0.8,
            ease: 'power3.out',
            scrollTrigger: {
                trigger: text,
                start: 'top 85%',
                toggleActions: 'play none none none'
            }
        });
    });
}

/**
 * Smooth scroll
 */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                gsap.to(window, {
                    duration: 1,
                    scrollTo: { y: target, offsetY: 80 },
                    ease: 'power3.inOut'
                });
            }
        });
    });
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAnimations);
} else {
    initAnimations();
}

// Export for external use
window.TraditionalAnimations = {
    init: initAnimations,
    scissorTransition: scissorCutTransition,
    bladeSwipe: bladeSwipeReveal
};
