// Sound engine -- procedural audio synthesis via Web Audio API
// No external audio files. All sounds generated from oscillators and noise buffers.

const sound = {
  ctx: null,        // AudioContext
  master: null,     // GainNode (master volume)
  engine: null,     // OscillatorNode (sawtooth)
  engineGain: null, // GainNode
  engine2: null,    // 2nd harmonic oscillator
  engine2Gain: null,
  aero: null,       // BufferSource for aero whoosh
  aeroGain: null,
  tireNode: null,   // BufferSource for tire squeal
  tireGain: null,
  tireBand: null,   // BiquadFilter (bandpass)
  crowd: null,      // BufferSource for crowd ambience
  crowdGain: null,
  muted: false,
  volume: 0.5,
  initialized: false,
};

function initAudio() {
  if (sound.initialized) return;
  sound.ctx = new (window.AudioContext || window.webkitAudioContext)();
  sound.master = sound.ctx.createGain();
  sound.master.gain.value = sound.volume;
  sound.master.connect(sound.ctx.destination);

  // Engine -- sawtooth oscillator at base 80 Hz
  sound.engine = sound.ctx.createOscillator();
  sound.engine.type = 'sawtooth';
  sound.engine.frequency.value = 80;
  sound.engineGain = sound.ctx.createGain();
  sound.engineGain.gain.value = 0;
  sound.engine.connect(sound.engineGain);
  sound.engineGain.connect(sound.master);
  sound.engine.start();

  // 2nd harmonic
  sound.engine2 = sound.ctx.createOscillator();
  sound.engine2.type = 'sawtooth';
  sound.engine2.frequency.value = 160;
  sound.engine2Gain = sound.ctx.createGain();
  sound.engine2Gain.gain.value = 0;
  sound.engine2.connect(sound.engine2Gain);
  sound.engine2Gain.connect(sound.master);
  sound.engine2.start();

  // Aero whoosh -- white noise through lowpass filter
  var aeroBuffer = createNoiseBuffer(sound.ctx, 2);
  sound.aero = sound.ctx.createBufferSource();
  sound.aero.buffer = aeroBuffer;
  sound.aero.loop = true;
  var aeroLow = sound.ctx.createBiquadFilter();
  aeroLow.type = 'lowpass';
  aeroLow.frequency.value = 400;
  sound.aeroGain = sound.ctx.createGain();
  sound.aeroGain.gain.value = 0;
  sound.aero.connect(aeroLow);
  aeroLow.connect(sound.aeroGain);
  sound.aeroGain.connect(sound.master);
  sound.aero.start();

  // Tire squeal -- white noise through bandpass filter
  var tireBuffer = createNoiseBuffer(sound.ctx, 2);
  sound.tireNode = sound.ctx.createBufferSource();
  sound.tireNode.buffer = tireBuffer;
  sound.tireNode.loop = true;
  sound.tireBand = sound.ctx.createBiquadFilter();
  sound.tireBand.type = 'bandpass';
  sound.tireBand.frequency.value = 3000;
  sound.tireBand.Q.value = 5;
  sound.tireGain = sound.ctx.createGain();
  sound.tireGain.gain.value = 0;
  sound.tireNode.connect(sound.tireBand);
  sound.tireBand.connect(sound.tireGain);
  sound.tireGain.connect(sound.master);
  sound.tireNode.start();

  // Crowd ambience -- brown noise at low volume
  var crowdBuffer = createBrownNoiseBuffer(sound.ctx, 4);
  sound.crowd = sound.ctx.createBufferSource();
  sound.crowd.buffer = crowdBuffer;
  sound.crowd.loop = true;
  sound.crowdGain = sound.ctx.createGain();
  sound.crowdGain.gain.value = 0.05;
  sound.crowd.connect(sound.crowdGain);
  sound.crowdGain.connect(sound.master);
  sound.crowd.start();

  initTurbo();
  sound.initialized = true;
}

function createNoiseBuffer(audioCtx, seconds) {
  var size = audioCtx.sampleRate * seconds;
  var buffer = audioCtx.createBuffer(1, size, audioCtx.sampleRate);
  var data = buffer.getChannelData(0);
  for (var i = 0; i < size; i++) {
    data[i] = Math.random() * 2 - 1;
  }
  return buffer;
}

function createBrownNoiseBuffer(audioCtx, seconds) {
  var size = audioCtx.sampleRate * seconds;
  var buffer = audioCtx.createBuffer(1, size, audioCtx.sampleRate);
  var data = buffer.getChannelData(0);
  var last = 0;
  for (var i = 0; i < size; i++) {
    var white = Math.random() * 2 - 1;
    data[i] = (last + 0.02 * white) / 1.02;
    last = data[i];
    data[i] *= 3.5;
  }
  return buffer;
}

function updateSound(replay, frameIdx) {
  if (!sound.initialized || !replay || sound.muted) return;

  var cars = replay.frames[frameIdx];
  if (!cars) return;

  var leader = cars.find(function(c) { return c.position === 1; });
  if (!leader) return;

  var t = sound.ctx.currentTime;
  var speed = leader.speed || 0;

  // Engine pitch: 80 Hz at 0 km/h, 400 Hz at 300 km/h
  var freq = 80 + (speed / 300) * 320;
  sound.engine.frequency.setTargetAtTime(freq, t, 0.05);
  sound.engine2.frequency.setTargetAtTime(freq * 2, t, 0.05);

  // Engine volume: scales with speed
  var engineVol = Math.min(0.15, speed / 300 * 0.15);
  sound.engineGain.gain.setTargetAtTime(engineVol, t, 0.05);
  sound.engine2Gain.gain.setTargetAtTime(engineVol * 0.3, t, 0.05);

  // Aero whoosh: scales with speed
  var aeroVol = Math.min(0.08, (speed / 300) * 0.08);
  sound.aeroGain.gain.setTargetAtTime(aeroVol, t, 0.1);

  // Tire squeal: curvature * speed
  var seg = leader.seg || 0;
  var curv = replay.track_curvatures ? (replay.track_curvatures[seg] || 0) : 0;
  var squealIntensity = curv * speed * 0.001;
  var squealVol = squealIntensity > 0.02 ? Math.min(0.12, squealIntensity) : 0;
  sound.tireGain.gain.setTargetAtTime(squealVol, t, 0.03);

  // Downshift pops: speed drop > 20 km/h between frames
  if (frameIdx > 0) {
    var prevCars = replay.frames[frameIdx - 1];
    var prevLeader = prevCars
      ? prevCars.find(function(c) { return c.name === leader.name; })
      : null;
    if (prevLeader) {
      var drop = prevLeader.speed - leader.speed;
      if (drop > 20) triggerDownshiftPop();
      if (drop > 30) triggerTurboWhistle(drop);
    }
  }
}

function triggerDownshiftPop() {
  if (!sound.initialized) return;
  var buf = createNoiseBuffer(sound.ctx, 0.05);
  var src = sound.ctx.createBufferSource();
  src.buffer = buf;
  var gain = sound.ctx.createGain();
  gain.gain.value = 0.1;
  gain.gain.setTargetAtTime(0, sound.ctx.currentTime + 0.02, 0.01);
  src.connect(gain);
  gain.connect(sound.master);
  src.start();
  src.stop(sound.ctx.currentTime + 0.05);
}

// ─── Spatial Audio (Sprint 14) ──────────────────────────────────────────────
var _carAudioSlots = [];

function initSpatialAudio(numCars) {
  if (!sound.initialized) return;
  _carAudioSlots = [];
  var maxSlots = Math.min(numCars || 5, 5);
  for (var i = 0; i < maxSlots; i++) {
    var osc = sound.ctx.createOscillator();
    osc.type = 'sawtooth';
    osc.frequency.value = 80;
    var gain = sound.ctx.createGain();
    gain.gain.value = 0;
    osc.connect(gain);
    gain.connect(sound.master);
    osc.start();
    _carAudioSlots.push({ osc: osc, gain: gain, name: null });
  }
}

function updateSpatialAudio(cars, cameraX, cameraY) {
  if (!sound.initialized || _carAudioSlots.length === 0) return;
  var t = sound.ctx.currentTime;
  var sorted = cars.slice().sort(function(a, b) {
    var da = Math.hypot((a.x || 0) - (cameraX || 0), (a.y || 0) - (cameraY || 0));
    var db = Math.hypot((b.x || 0) - (cameraX || 0), (b.y || 0) - (cameraY || 0));
    return da - db;
  });
  for (var i = 0; i < _carAudioSlots.length; i++) {
    var slot = _carAudioSlots[i];
    var car = sorted[i];
    if (!car) { slot.gain.gain.setTargetAtTime(0, t, 0.05); continue; }
    var dist = Math.hypot((car.x || 0) - (cameraX || 0), (car.y || 0) - (cameraY || 0));
    var vol = Math.min(0.12, 1.0 / (1.0 + dist * 0.01) * 0.12);
    var freq = 80 + ((car.speed || 0) / 300) * 320;
    slot.osc.frequency.setTargetAtTime(freq, t, 0.05);
    slot.gain.gain.setTargetAtTime(vol, t, 0.05);
    slot.name = car.name;
  }
}

// ─── Turbo Whistle (Sprint 14) ──────────────────────────────────────────────
var _turboOsc = null;
var _turboGain = null;

function initTurbo() {
  if (!sound.ctx) return;
  _turboOsc = sound.ctx.createOscillator();
  _turboOsc.type = 'sine';
  _turboOsc.frequency.value = 2000;
  _turboGain = sound.ctx.createGain();
  _turboGain.gain.value = 0;
  _turboOsc.connect(_turboGain);
  _turboGain.connect(sound.master);
  _turboOsc.start();
}

function triggerTurboWhistle(speedDrop) {
  if (!sound.initialized || !_turboOsc) return;
  var t = sound.ctx.currentTime;
  var mag = Math.min(1.0, (speedDrop || 30) / 100);
  _turboOsc.frequency.setValueAtTime(4000, t);
  _turboOsc.frequency.linearRampToValueAtTime(2000, t + 0.3);
  _turboGain.gain.setValueAtTime(mag * 0.06, t);
  _turboGain.gain.linearRampToValueAtTime(0, t + 0.3);
}

// ─── Drama-Driven Crowd (Sprint 14) ────────────────────────────────────────
var _dramaScore = 0.1;

function updateDramaScore(events, currentTick) {
  _dramaScore = 0.1;
  if (!events) return;
  for (var i = 0; i < events.length; i++) {
    var e = events[i];
    var age = currentTick - (e.tick || 0);
    if (age < 0 || age > 150) continue; // within 5 seconds
    if (e.type === 'OVERTAKE') _dramaScore += 0.4 * Math.max(0, 1 - age / 90);
    else if (e.type === 'BATTLE') _dramaScore += 0.2;
    else if (e.type === 'SAFETY_CAR') _dramaScore += 0.3 * Math.max(0, 1 - age / 150);
    else if (e.type === 'SPIN') _dramaScore += 0.5 * Math.max(0, 1 - age / 60);
    else if (e.type === 'FASTEST_LAP') _dramaScore += 0.2 * Math.max(0, 1 - age / 60);
  }
  _dramaScore = Math.min(1.0, _dramaScore);
}

function triggerCrowdSwell(magnitude) {
  if (!sound.initialized || !sound.crowdGain) return;
  var t = sound.ctx.currentTime;
  var mag = magnitude || _dramaScore;
  sound.crowdGain.gain.setTargetAtTime(0.05 + mag * 0.25, t, 0.1);
  sound.crowdGain.gain.setTargetAtTime(0.05, t + 0.5, 0.3);
}

// ─── Camera-Aware Mix (Sprint 14) ──────────────────────────────────────────
var _mixProfiles = {
  full:    { engine: 0.2, crowd: 0.8, aero: 0.1, tire: 0.1, turbo: 0.1 },
  follow:  { engine: 0.6, crowd: 0.4, aero: 0.3, tire: 0.2, turbo: 0.3 },
  onboard: { engine: 1.0, crowd: 0.1, aero: 0.5, tire: 0.4, turbo: 0.5 },
};

function setCameraMix(mode) {
  if (!sound.initialized) return;
  var p = _mixProfiles[mode] || _mixProfiles.follow;
  var t = sound.ctx.currentTime;
  if (sound.engineGain) sound.engineGain.gain.setTargetAtTime(0.15 * p.engine, t, 0.2);
  if (sound.crowdGain) sound.crowdGain.gain.setTargetAtTime(0.1 * p.crowd, t, 0.2);
  if (sound.aeroGain) sound.aeroGain.gain.setTargetAtTime(0.08 * p.aero, t, 0.2);
  if (sound.tireGain) sound.tireGain.gain.setTargetAtTime(0.12 * p.tire, t, 0.2);
  if (_turboGain) _turboGain.gain.setTargetAtTime(0.06 * p.turbo, t, 0.2);
}

function pauseSound() {
  if (!sound.initialized) return;
  var t = sound.ctx.currentTime;
  sound.engineGain.gain.setTargetAtTime(0, t, 0.05);
  sound.engine2Gain.gain.setTargetAtTime(0, t, 0.05);
  sound.aeroGain.gain.setTargetAtTime(0, t, 0.05);
  sound.tireGain.gain.setTargetAtTime(0, t, 0.05);
}

function setVolume(vol) {
  sound.volume = vol;
  if (sound.master) {
    sound.master.gain.setTargetAtTime(vol, sound.ctx.currentTime, 0.05);
  }
}

function toggleMute() {
  sound.muted = !sound.muted;
  if (sound.master) {
    sound.master.gain.setTargetAtTime(
      sound.muted ? 0 : sound.volume, sound.ctx.currentTime, 0.05
    );
  }
}
