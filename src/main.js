import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import * as THREE from 'three';
import { createProteinTub } from './tub.js';

gsap.registerPlugin(ScrollTrigger);

const canvas = document.querySelector('#scene');
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  alpha: true,
  powerPreference: 'high-performance',
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.15;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(
  40,
  window.innerWidth / window.innerHeight,
  0.1,
  100
);
camera.position.set(0, 0.35, 7.2);

const hemi = new THREE.HemisphereLight(0xf3f7fa, 0x5d7388, 1.15);
scene.add(hemi);

const key = new THREE.DirectionalLight(0xffffff, 1.35);
key.position.set(4, 6, 5);
scene.add(key);

const fill = new THREE.DirectionalLight(0xb8e83a, 0.35);
fill.position.set(-5, 2, -2);
scene.add(fill);

const rim = new THREE.DirectionalLight(0xd7e2ea, 0.55);
rim.position.set(-2, 3, 6);
scene.add(rim);

const tub = createProteinTub();
tub.position.set(1.35, -0.15, 0);
tub.rotation.set(0.12, -0.55, 0.08);
scene.add(tub);

const stage = {
  x: 1.35,
  y: -0.15,
  z: 0,
  rotX: 0.12,
  rotY: -0.55,
  rotZ: 0.08,
  scale: 1,
  camZ: 7.2,
};

function applyStage() {
  tub.position.set(stage.x, stage.y, stage.z);
  tub.rotation.set(stage.rotX, stage.rotY, stage.rotZ);
  tub.scale.setScalar(stage.scale);
  camera.position.z = stage.camZ;
}

function isMobile() {
  return window.innerWidth < 900;
}

function layoutForViewport() {
  if (isMobile()) {
    stage.x = 0;
    stage.y = 0.55;
    stage.scale = 0.82;
    stage.camZ = 8.2;
  } else {
    stage.x = 1.35;
    stage.y = -0.15;
    stage.scale = 1;
    stage.camZ = 7.2;
  }
  applyStage();
}

layoutForViewport();

let floatTween;
function startIdleFloat() {
  if (prefersReducedMotion) return;
  floatTween?.kill();
  floatTween = gsap.to(tub.position, {
    y: stage.y + 0.12,
    duration: 2.8,
    ease: 'sine.inOut',
    yoyo: true,
    repeat: -1,
  });
}

function stopIdleFloat() {
  floatTween?.kill();
}

function introAnimation() {
  const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });

  gsap.set('.brand', { y: 48, opacity: 0 });
  gsap.set('.hero h1', { y: 36, opacity: 0 });
  gsap.set('.lede', { y: 28, opacity: 0 });
  gsap.set('.cta-row', { y: 20, opacity: 0 });
  gsap.set('.scroll-hint', { opacity: 0 });
  gsap.set('.site-header', { y: -24, opacity: 0 });

  const startY = stage.y - 1.4;
  tub.position.y = startY;
  tub.rotation.y = stage.rotY - 1.2;
  tub.scale.setScalar(stage.scale * 0.72);

  tl.to('.site-header', { y: 0, opacity: 1, duration: 0.8 }, 0)
    .to(
      tub.position,
      {
        y: stage.y,
        duration: 1.4,
        ease: 'power4.out',
        onComplete: startIdleFloat,
      },
      0.15
    )
    .to(
      tub.rotation,
      {
        y: stage.rotY,
        duration: 1.5,
        ease: 'power3.out',
      },
      0.15
    )
    .to(
      tub.scale,
      {
        x: stage.scale,
        y: stage.scale,
        z: stage.scale,
        duration: 1.35,
        ease: 'power3.out',
      },
      0.15
    )
    .to('.brand', { y: 0, opacity: 1, duration: 0.9 }, 0.35)
    .to('.hero h1', { y: 0, opacity: 1, duration: 0.85 }, 0.48)
    .to('.lede', { y: 0, opacity: 1, duration: 0.8 }, 0.58)
    .to('.cta-row', { y: 0, opacity: 1, duration: 0.75 }, 0.68)
    .to('.scroll-hint', { opacity: 1, duration: 0.6 }, 0.95);

  if (prefersReducedMotion) {
    tl.progress(1);
    startIdleFloat();
  }
}

function setupScrollStory() {
  const mm = gsap.matchMedia();

  mm.add('(min-width: 900px)', () => {
    const desktop = gsap.timeline({
      scrollTrigger: {
        trigger: 'main',
        start: 'top top',
        end: 'bottom bottom',
        scrub: 1.1,
        onUpdate: (self) => {
          if (self.progress > 0.02) stopIdleFloat();
          else if (!floatTween || !floatTween.isActive()) startIdleFloat();
        },
      },
    });

    desktop
      .to(stage, {
        x: 1.55,
        y: 0.05,
        rotY: 0.85,
        rotX: 0.05,
        scale: 1.08,
        camZ: 6.4,
        duration: 1,
        onUpdate: applyStage,
      })
      .to(stage, {
        x: -1.5,
        y: 0.1,
        rotY: 2.4,
        rotX: -0.08,
        rotZ: -0.05,
        scale: 1.12,
        camZ: 6.1,
        duration: 1,
        onUpdate: applyStage,
      })
      .to(stage, {
        x: 0,
        y: 0.2,
        rotY: 4.2,
        rotX: 0.18,
        rotZ: 0,
        scale: 1.28,
        camZ: 5.5,
        duration: 1,
        onUpdate: applyStage,
      });

    return () => desktop.scrollTrigger?.kill();
  });

  mm.add('(max-width: 899px)', () => {
    const mobile = gsap.timeline({
      scrollTrigger: {
        trigger: 'main',
        start: 'top top',
        end: 'bottom bottom',
        scrub: 1,
        onUpdate: (self) => {
          if (self.progress > 0.02) stopIdleFloat();
          else if (!floatTween || !floatTween.isActive()) startIdleFloat();
        },
      },
    });

    mobile
      .to(stage, {
        x: 0,
        y: 0.2,
        rotY: 0.9,
        scale: 0.9,
        camZ: 7.4,
        duration: 1,
        onUpdate: applyStage,
      })
      .to(stage, {
        x: 0,
        y: 0.15,
        rotY: 2.5,
        scale: 0.95,
        camZ: 7.0,
        duration: 1,
        onUpdate: applyStage,
      })
      .to(stage, {
        x: 0,
        y: 0.25,
        rotY: 4.1,
        scale: 1.05,
        camZ: 6.4,
        duration: 1,
        onUpdate: applyStage,
      });

    return () => mobile.scrollTrigger?.kill();
  });

  gsap.utils.toArray('.panel-copy').forEach((el) => {
    gsap.from(el, {
      y: 56,
      opacity: 0,
      duration: 1,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: el,
        start: 'top 80%',
        toggleActions: 'play none none reverse',
      },
    });
  });
}

function onResize() {
  const w = window.innerWidth;
  const h = window.innerHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  renderer.setSize(w, h);
  layoutForViewport();
  ScrollTrigger.refresh();
}

window.addEventListener('resize', onResize);

const clock = new THREE.Clock();

function animate() {
  requestAnimationFrame(animate);
  const t = clock.getElapsedTime();
  if (!ScrollTrigger.isTouch && prefersReducedMotion === false) {
    tub.rotation.z = stage.rotZ + Math.sin(t * 0.6) * 0.02;
  }
  renderer.render(scene, camera);
}

introAnimation();
setupScrollStory();
animate();
