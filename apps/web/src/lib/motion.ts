/**
 * Shared framer-motion variants for the LexGuard editorial aesthetic.
 *
 * The animations lean on physical metaphors: a verdict "falls" onto the page,
 * an agent argument "types in" like a teletype, severity badges "stamp" like
 * a court seal.
 */

import type { Variants } from 'framer-motion';

export const EASE_OUT = [0.16, 1, 0.3, 1] as const;
export const EASE_IN = [0.7, 0, 0.84, 0] as const;

export const fadeUp: Variants = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.7, ease: EASE_OUT },
  },
};

export const fadeIn: Variants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { duration: 0.5, ease: EASE_OUT } },
};

export const stagger = (delayChildren = 0, staggerChildren = 0.07): Variants => ({
  hidden: {},
  visible: {
    transition: { delayChildren, staggerChildren },
  },
});

export const ruleSweep: Variants = {
  hidden: { scaleX: 0, originX: 0 },
  visible: { scaleX: 1, transition: { duration: 0.9, ease: EASE_OUT, delay: 0.1 } },
};

export const drop: Variants = {
  hidden: { opacity: 0, y: -40, rotate: -1 },
  visible: {
    opacity: 1,
    y: 0,
    rotate: 0,
    transition: { type: 'spring', stiffness: 220, damping: 22, mass: 1.1 },
  },
};

export const stamp: Variants = {
  hidden: { opacity: 0, scale: 1.6, rotate: -8 },
  visible: {
    opacity: 1,
    scale: 1,
    rotate: -3,
    transition: { duration: 0.45, ease: EASE_IN },
  },
};

export const slideRight: Variants = {
  hidden: { opacity: 0, x: -16 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.55, ease: EASE_OUT } },
};
