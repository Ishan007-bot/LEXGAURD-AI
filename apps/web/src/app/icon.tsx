import { ImageResponse } from 'next/og';

export const runtime = 'edge';
export const size = { width: 32, height: 32 };
export const contentType = 'image/png';

export default function Icon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          background: '#0e0e0e',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          gap: 2,
          position: 'relative',
        }}
      >
        <div style={{ width: 22, height: 2, background: '#f5f0e6' }} />
        <div style={{ width: 22, height: 2, background: '#f5f0e6' }} />
        <div style={{ width: 22, height: 3, background: '#c5272d' }} />
        <div style={{ width: 22, height: 2, background: '#f5f0e6' }} />
        <div style={{ width: 22, height: 2, background: '#f5f0e6' }} />
      </div>
    ),
    { ...size },
  );
}
