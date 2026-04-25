import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  scenarios: {
    smoke: {
      executor: 'constant-vus',
      vus: 10,
      duration: '2m',
      tags: { test_type: 'smoke' },
    },
    soak: {
      executor: 'constant-vus',
      vus: 50,
      duration: '10m',
      startTime: '2m30s',
      tags: { test_type: 'soak' },
    },
    spike: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '30s', target: 200 },
        { duration: '1m', target: 200 },
        { duration: '30s', target: 0 },
      ],
      startTime: '13m',
      tags: { test_type: 'spike' },
    },
    // Chaos-style turbulence — intermittent packet loss + latency
    chaos: {
      executor: 'ramping-vus',
      startVUs: 10,
      stages: [
        { duration: '2m', target: 10 },
        { duration: '2m', target: 50 },
        { duration: '2m', target: 10 },
      ],
      startTime: '15m',
      tags: { test_type: 'chaos' },
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function () {
  const endpoints = [
    { url: `${BASE_URL}/api/v1/health`, method: 'GET' },
    { url: `${BASE_URL}/api/v1/health/ready`, method: 'GET' },
    { url: `${BASE_URL}/api/v1/health/live`, method: 'GET' },
  ];

  for (const endpoint of endpoints) {
    const res = http.request(endpoint.method, endpoint.url);
    check(res, {
      'status is 200': (r) => r.status === 200,
      'response time < 500ms': (r) => r.timings.duration < 500,
    });
  }

  sleep(1);
}
