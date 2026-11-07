'use client';

import dynamic from 'next/dynamic';

const AgentNodeNetwork = dynamic(() => import('@/components/AgentNodeNetwork'), {
  ssr: false,
});

export default function CanvasWrapper() {
  return <AgentNodeNetwork />;
}

