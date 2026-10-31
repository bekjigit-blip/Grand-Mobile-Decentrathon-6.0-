import express from 'express';
import { createServer as createViteServer } from 'vite';
import { spawn } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const PORT = parseInt(process.env.PORT || '3000', 10);
const PYTHON_PORT = parseInt(process.env.PORT_BACKEND || '8005', 10);

// Configurable Python interpreter for Windows venv and Linux
const isWin = process.platform === 'win32';
const defaultPython = isWin
  ? (fs.existsSync(path.join(__dirname, 'venv', 'Scripts', 'python.exe'))
      ? path.join(__dirname, 'venv', 'Scripts', 'python.exe')
      : 'python')
  : (fs.existsSync(path.join(__dirname, 'venv', 'bin', 'python'))
      ? path.join(__dirname, 'venv', 'bin', 'python')
      : 'python3');

const pythonExecutable = process.env.PYTHON_PATH || defaultPython;

console.log(`[Server] Using Python interpreter: ${pythonExecutable}`);
console.log(`[Server] Starting Python FastAPI backend (app.server) on port ${PYTHON_PORT}...`);

const pythonProcess = spawn(pythonExecutable, ['-m', 'app.server'], {
  cwd: __dirname,
  env: { ...process.env, PYTHONPATH: '.' },
  stdio: 'inherit'
});

pythonProcess.on('error', (err) => {
  console.error('[Server] Failed to start Python backend:', err);
});

pythonProcess.on('exit', (code, signal) => {
  console.log(`[Server] Python backend exited with code ${code}, signal ${signal}`);
});

process.on('exit', () => {
  pythonProcess.kill();
});

async function createServer() {
  const app = express();
  app.use(express.json({ limit: '50mb' }));
  app.use(express.urlencoded({ extended: true, limit: '50mb' }));

  // Helper proxy handler using Node's native fetch
  const forwardToPython = async (req: express.Request, res: express.Response) => {
    const targetUrl = `http://127.0.0.1:${PYTHON_PORT}${req.originalUrl}`;
    try {
      const options: RequestInit = {
        method: req.method,
        headers: {
          'Content-Type': req.headers['content-type'] || 'application/json',
          'Accept': req.headers['accept'] || 'application/json',
        },
      };

      if (['POST', 'PUT', 'PATCH'].includes(req.method) && req.body) {
        options.body = JSON.stringify(req.body);
      }

      const pythonRes = await fetch(targetUrl, options);
      const data = await pythonRes.json();
      res.status(pythonRes.status).json(data);
    } catch (err: any) {
      res.status(502).json({
        error: 'Python backend is unavailable or starting',
        details: err?.message,
        targetUrl
      });
    }
  };

  // API and Decentrathon triage routes
  app.post('/triage', forwardToPython);
  app.get('/health', forwardToPython);
  app.all('/api/*', forwardToPython);

  // Vite development middleware
  const isProd = process.env.NODE_ENV === 'production';
  if (!isProd) {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    app.use(express.static(path.resolve(__dirname, 'dist')));
    app.get('*', (_req, res) => {
      res.sendFile(path.resolve(__dirname, 'dist', 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`[Server] Support Copilot running at http://0.0.0.0:${PORT}`);
    console.log(`[Server] Direct FastAPI backend at http://127.0.0.1:${PYTHON_PORT}`);
  });
}

createServer().catch((err) => {
  console.error('[Server] Server bootstrap failed:', err);
});
