const navToggle = document.querySelector('[data-nav-toggle]');
const navPanel = document.querySelector('[data-nav-panel]');
if (navToggle && navPanel) {
    navToggle.addEventListener('click', () => navPanel.classList.toggle('is-open'));
}

document.querySelectorAll('[data-dismiss-alert]').forEach((button) => {
    button.addEventListener('click', () => button.closest('.alert')?.remove());
});

function getCookie(name) {
    return document.cookie.split('; ').find((row) => row.startsWith(`${name}=`))?.split('=')[1];
}

const wheel = document.querySelector('[data-wheel]');
const spinButton = document.querySelector('[data-wheel-spin]');
const result = document.querySelector('[data-wheel-result]');
if (wheel && spinButton && result) {
    spinButton.addEventListener('click', async () => {
        spinButton.disabled = true;
        result.textContent = '';
        const response = await fetch(spinButton.dataset.spinUrl, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') || '' },
        });
        const data = await response.json();
        const fullSpins = 2160;
        const winningAngles = data.reward === 'shipping' ? [210, 30] : [330, 90];
        const wobble = Math.floor(Math.random() * 16) - 8;
        const angle = fullSpins + winningAngles[Math.floor(Math.random() * winningAngles.length)] + wobble;
        wheel.style.transform = `rotate(${angle}deg)`;
        setTimeout(() => {
            result.textContent = data.message || 'Reward already claimed.';
            spinButton.textContent = 'Claimed';
        }, 4100);
    });
}

const dismissWheel = document.querySelector('[data-wheel-dismiss]');
if (dismissWheel) {
    dismissWheel.addEventListener('click', async () => {
        await fetch('/wheel/dismiss/');
        document.querySelector('[data-wheel-modal]')?.remove();
    });
}

const promoInput = document.querySelector('[data-promo-input]');
if (promoInput) {
    let promoTimer;
    promoInput.addEventListener('input', () => {
        clearTimeout(promoTimer);
        promoTimer = setTimeout(() => {
            if (promoInput.value.trim().length >= 8 || promoInput.value.trim().length === 0) {
                const applyButton = promoInput.closest('form')?.querySelector('button[name="apply_promo"]');
                applyButton?.click();
            }
        }, 900);
    });
}
