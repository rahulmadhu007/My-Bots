import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import * as THREE from 'three';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { createPowderParticles, createProteinTub } from './tub.js';

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
renderer.toneMappingExposure = 1.22;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(
  38,
  window.innerWidth / window.innerHeight,
  0.1,
  100
);
camera.position.set(0, 0.4, 7.1);

const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

const hemi = new THREE.HemisphereLight(0xfff6ea, 0x6a5a48, 0.85);
scene.add(hemi);

const key = new THREE.DirectionalLight(0xfff2df, 1.55);
key.position.set(4.5, 7, 4.5);
key.castShadow = true;
key.shadow.mapSize.set(2048, 2048);
key.shadow.camera.near = 1;
key.shadow.camera.far = 24;
key.shadow.camera.left = -6;
key.shadow.camera.right = 6;
key.shadow.camera.top = 6;
key.shadow.camera.bottom = -6;
key.shadow.bias = -0.0002;
scene.add(key);

const fill = new THREE.DirectionalLight(0xc9a35b, 0.45);
fill.position.set(-5.5, 2.5, -1.5);
scene.add(fill);

const rim = new THREE.DirectionalLight(0xf7efe2, 0.7);
rim.position.set(-1.5, 3.5, 6.5);
scene.add(rim);

const floor = new THREE.Mesh(
  new THREE.CircleGeometry(4.5, 64),
  new THREE.ShadowMaterial({ opacity: 0.22 })
);
floor.rotation.x = -Math.PI / 2;
floor.position.y = -1.42;
floor.receiveShadow = true;
scene.add(floor);

const tub = createProteinTub();
tub.position.set(1.4, -0.1, 0);
tub.rotation.set(0.1, -0.55, 0.06);
scene.add(tub);

const particles = createPowderParticles();
scene.add(particles);

const stage = {
  x: 1.4,
  y: -0.1,
  z: 0,
  rotX: 0.1,
  rotY: -0.55,
  rotZ: 0.06,
  scale: 1,
  camZ: 7.1,
  exposure: 1.22,
};

const pointer = { x: 0, y: 0, tx: 0, ty: 0 };

function applyStage() {
  tub.position.set(stage.x, stage.y, stage.z);
  tub.rotation.set(stage.rotX, stage.rotY, stage.rotZ);
  tub.scale.setScalar(stage.scale);
  camera.position.z = stage.camZ;
  renderer.toneMappingExposure = stage.exposure;
}

function isMobile() {
  return window.innerWidth < 900;
}

function layoutForViewport() {
  if (isMobile()) {
    stage.x = 0;
    stage.y = 0.55;
    stage.scale = 0.84;
    stage.camZ = 8.1;
  } else {
    stage.x = 1.4;
    stage.y = -0.1;
    stage.scale = 1;
    stage.camZ = 7.1;
  }
  applyStage();
}

layoutForViewport();

let floatTween;
function startIdleFloat() {
  if (prefersReducedMotion) return;
  floatTween?.kill();
  floatTween = gsap.to(tub.position, {
    y: stage.y + 0.14,
    duration: 3.2,
    ease: 'sine.inOut',
    yoyo: true,
    repeat: -1,
  });
  gsap.to(tub.rotation, {
    z: stage.rotZ + 0.04,
    duration: 3.6,
    ease: 'sine.inOut',
    yoyo: true,
    repeat: -1,
  });
}

function stopIdleFloat() {
  floatTween?.kill();
  gsap.killTweensOf(tub.rotation);
}

function introAnimation() {
  const tl = gsap.timeline({ defaults: { ease: 'power3.out' } });

  gsap.set('.brand', { y: 56, opacity: 0, filter: 'blur(8px)' });
  gsap.set('.hero h1', { y: 40, opacity: 0 });
  gsap.set('.lede', { y: 28, opacity: 0 });
  gsap.set('.cta-row', { y: 22, opacity: 0 });
  gsap.set('.scroll-hint', { opacity: 0 });
  gsap.set('.site-header', { y: -24, opacity: 0 });
  gsap.set(particles.material, { opacity: 0 });

  tub.position.y = stage.y - 1.6;
  tub.rotation.y = stage.rotY - 1.35;
  tub.scale.setScalar(stage.scale * 0.68);

  tl.to('.site-header', { y: 0, opacity: 1, duration: 0.9 }, 0)
    .to(
      tub.position,
      {
        y: stage.y,
        duration: 1.55,
        ease: 'power4.out',
        onComplete: startIdleFloat,
      },
      0.12
    )
    .to(tub.rotation, { y: stage.rotY, duration: 1.65, ease: 'power3.out' }, 0.12)
    .to(
      tub.scale,
      {
        x: stage.scale,
        y: stage.scale,
        z: stage.scale,
        duration: 1.45,
        ease: 'power3.out',
      },
      0.12
    )
    .to(particles.material, { opacity: 0.38, duration: 1.2 }, 0.4)
    .to('.brand', { y: 0, opacity: 1, filter: 'blur(0px)', duration: 1 }, 0.38)
    .to('.hero h1', { y: 0, opacity: 1, duration: 0.9 }, 0.52)
    .to('.lede', { y: 0, opacity: 1, duration: 0.85 }, 0.62)
    .to('.cta-row', { y: 0, opacity: 1, duration: 0.8 }, 0.72)
    .to('.scroll-hint', { opacity: 1, duration: 0.6 }, 1);

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
        scrub: 1.15,
        onUpdate: (self) => {
          if (self.progress > 0.02) stopIdleFloat();
          else if (!floatTween || !floatTween.isActive()) startIdleFloat();
        },
      },
    });

    desktop
      .to(stage, {
        x: 1.65,
        y: 0.08,
        rotY: 0.95,
        rotX: 0.04,
        scale: 1.1,
        camZ: 6.2,
        exposure: 1.28,
        duration: 1,
        onUpdate: applyStage,
      })
      .to(stage, {
        x: -1.55,
        y: 0.12,
        rotY: 2.55,
        rotX: -0.1,
        rotZ: -0.06,
        scale: 1.16,
        camZ: 5.9,
        exposure: 1.18,
        duration: 1,
        onUpdate: applyStage,
      })
      .to(stage, {
        x: 0,
        y: 0.22,
        rotY: 4.4,
        rotX: 0.2,
        rotZ: 0,
        scale: 1.34,
        camZ: 5.25,
        exposure: 1.32,
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
        y: 0.22,
        rotY: 1.0,
        scale: 0.92,
        camZ: 7.3,
        duration: 1,
        onUpdate: applyStage,
      })
      .to(stage, {
        x: 0,
        y: 0.18,
        rotY: 2.6,
        scale: 0.98,
        camZ: 6.9,
        duration: 1,
        onUpdate: applyStage,
      })
      .to(stage, {
        x: 0,
        y: 0.28,
        rotY: 4.3,
        scale: 1.08,
        camZ: 6.25,
        duration: 1,
        onUpdate: applyStage,
      });

    return () => mobile.scrollTrigger?.kill();
  });

  gsap.utils.toArray('.panel-copy').forEach((el) => {
    gsap.from(el, {
      y: 64,
      opacity: 0,
      duration: 1.1,
      ease: 'power3.out',
      scrollTrigger: {
        trigger: el,
        start: 'top 78%',
        toggleActions: 'play none none reverse',
      },
    });
  });

  gsap.utils.toArray('.atmosphere img').forEach((img) => {
    gsap.fromTo(
      img,
      { scale: 1.12, yPercent: 6 },
      {
        scale: 1,
        yPercent: -4,
        ease: 'none',
        scrollTrigger: {
          trigger: img.closest('.panel'),
          start: 'top bottom',
          end: 'bottom top',
          scrub: true,
        },
      }
    );
  });
}

function onPointerMove(event) {
  const x = event.touches ? event.touches[0].clientX : event.clientX;
  const y = event.touches ? event.touches[0].clientY : event.clientY;
  pointer.tx = (x / window.innerWidth - 0.5) * 2;
  pointer.ty = (y / window.innerHeight - 0.5) * 2;
}

window.addEventListener('pointermove', onPointerMove, { passive: true });

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
  const dt = Math.min(clock.getDelta(), 0.05);
  const t = clock.elapsedTime;

  pointer.x += (pointer.tx - pointer.x) * 0.06;
  pointer.y += (pointer.ty - pointer.y) * 0.06;

  if (!prefersReducedMotion) {
    camera.position.x = pointer.x * 0.28;
    camera.position.y = 0.4 - pointer.y * 0.16;
    camera.lookAt(tub.position.x * 0.35, tub.position.y * 0.2, 0);

    const pos = particles.geometry.attributes.position;
    const speeds = particles.userData.speeds;
    for (let i = 0; i < speeds.length; i += 1) {
      pos.array[i * 3 + 1] += speeds[i] * dt;
      if (pos.array[i * 3 + 1] > 3.2) {
        const angle = Math.random() * Math.PI * 2;
        const radius = 1.8 + Math.random() * 2.4;
        pos.array[i * 3 + 1] = -1.2;
        pos.array[i * 3] = Math.cos(angle) * radius;
        pos.array[i * 3 + 2] = Math.sin(angle) * radius * 0.55;
      }
    }
    pos.needsUpdate = true;
    particles.rotation.y = t * 0.03;
  }

  renderer.render(scene, camera);
}

introAnimation();
setupScrollStory();
animate();
