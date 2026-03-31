import { useEffect, useRef } from 'react';

export default function useWaveform(fileUrl, canvasRef, audioRef) {
  const audioCtxRef = useRef(null);
  const analyserRef = useRef(null);
  const sourceRef = useRef(null);
  const animationRef = useRef(null);

  useEffect(() => {
    if (!fileUrl || !canvasRef.current || !audioRef.current) return;

    const audio = audioRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    // Create context on user interaction to avoid auto-play policy issues in some browsers
    // but typically if audio is playing, context is fine to create.
    if (!audioCtxRef.current) {
      audioCtxRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }
    const audioCtx = audioCtxRef.current;

    if (!analyserRef.current) {
      analyserRef.current = audioCtx.createAnalyser();
      analyserRef.current.fftSize = 256;
    }
    const analyser = analyserRef.current;

    // Connect source to analyser only once per audio element
    if (!sourceRef.current) {
      try {
        sourceRef.current = audioCtx.createMediaElementSource(audio);
        sourceRef.current.connect(analyser);
        analyser.connect(audioCtx.destination);
      } catch {
        // Already connected
      }
    }

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const draw = () => {
      animationRef.current = requestAnimationFrame(draw);

      analyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.fillStyle = '#7b6ef6';

      const barWidth = Math.max(2, (canvas.width / bufferLength) * 2.5);
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height;
        ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);
        x += barWidth + 1;
      }
    };

    const attemptResume = () => {
      if (audioCtx.state === 'suspended') {
        audioCtx.resume();
      }
    };

    audio.addEventListener('play', attemptResume);
    draw();

    return () => {
      if (animationRef.current) cancelAnimationFrame(animationRef.current);
      audio.removeEventListener('play', attemptResume);
      // We don't disconnect nodes to reuse them if src changes on same audio element.
    };
  }, [fileUrl, canvasRef, audioRef]);
}
