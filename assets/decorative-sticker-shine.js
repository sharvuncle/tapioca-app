"use strict";

document.addEventListener("DOMContentLoaded", () => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        return;
    }

    const images = document.querySelectorAll(
        "img.campaign-sticker[data-free-sticker]"
    );

    const visible = new Set();
    const timers = new Map();

    function schedule(sticker) {
        if (!visible.has(sticker)) return;

        // Each sticker gets its own random wait of 5 to 16 seconds.
        const delay = 1000 + Math.random() * 3000;

        const timer = window.setTimeout(() => {
            timers.delete(sticker);

            if (!visible.has(sticker)) return;

            // Randomly reverse the reflection's direction.
            const reverse = Math.random() < 0.5;

            sticker.style.setProperty(
                "--shine-from", reverse ? "-150%" : "150%"
            );

            sticker.style.setProperty(
                "--shine-to", reverse ? "150%" : "-150%"
            );

            sticker.classList.add("sticker-shining");

            const finishTimer = window.setTimeout(() => {
                sticker.classList.remove("sticker-shining");
                timers.delete(sticker);

                if (visible.has(sticker)) {
                    schedule(sticker);
                }
            }, 1150);

            timers.set(sticker, finishTimer);
        }, delay);

        timers.set(sticker, timer);
    }

    const observer = new IntersectionObserver(entries => {
        for (const entry of entries) {
            const sticker = entry.target;

            if (entry.isIntersecting) {
                if (!visible.has(sticker)) {
                    visible.add(sticker);
                    schedule(sticker);
                }
            } else {
                visible.delete(sticker);

                if (timers.has(sticker)) {
                    window.clearTimeout(timers.get(sticker));
                    timers.delete(sticker);
                }

                sticker.classList.remove("sticker-shining");
            }
        }
    }, {
        rootMargin: "40px"
    });

    // Wrap existing decorative images so CSS can draw
    // a shine on top, without replacing or moving the images.
    for (const image of images) {
        const wrapper = document.createElement("button");

        wrapper.className = image.className;
        wrapper.dataset.freeSticker = image.dataset.freeSticker;
        wrapper.type = "button";
        wrapper.setAttribute(
            "aria-label",
            "Interactive Tapioca sticker"
        );

        image.className = "campaign-sticker-art";
        image.removeAttribute("data-free-sticker");

        image.parentNode.insertBefore(wrapper, image);
        wrapper.appendChild(image);

        // Give the wrapper a real height so its shine is visible.
        // Use a fallback until the image finishes loading.
        const tallSticker = [
            "faq-mascot",
            "footer-mascot"
        ].includes(wrapper.dataset.freeSticker);

        wrapper.style.aspectRatio = tallSticker ? "3 / 4" : "4 / 3";

        const updateStickerSize = () => {
            if (image.naturalWidth > 0 && image.naturalHeight > 0) {
                wrapper.style.aspectRatio =
                    `${image.naturalWidth} / ${image.naturalHeight}`;
            }
        };

        if (image.complete) {
            updateStickerSize();
        } else {
            image.addEventListener("load", updateStickerSize, {
                once: true
            });
        }

        observer.observe(wrapper);
    }
});