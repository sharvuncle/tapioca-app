import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn

from pymobiledevice3.tunneld.api import TUNNELD_DEFAULT_ADDRESS, get_tunneld_devices
from pymobiledevice3.services.dvt.instruments.location_simulation import LocationSimulation
from pymobiledevice3.services.dvt.instruments.dvt_provider import DvtProvider

rsd = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global rsd
    try:
        devices = await get_tunneld_devices(TUNNELD_DEFAULT_ADDRESS)
        if not devices:
            print("[!] No devices found via tunneld. Is 'python -m pymobiledevice3 remote tunneld' running?")
        else:
            rsd = devices[0]
            print(f"[✓] Connected to device via tunneld: {rsd.udid}")
    except Exception as e:
        print(f"[!] Could not connect via tunneld: {e}")
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class RouteManager:
    def __init__(self):
        self.running = False
        self.paused = False
        self.current_task = None
        self.current_pos = None
        self._sim = None

    async def _get_sim(self, fresh=False):
        global rsd
        if fresh or self._sim is None:
            self._sim = None
            if rsd is None:
                devices = await get_tunneld_devices(TUNNELD_DEFAULT_ADDRESS)
                if not devices:
                    raise RuntimeError("No devices found via tunneld")
                rsd = devices[0]
            provider = DvtProvider(rsd)
            sim = LocationSimulation(provider)
            await sim.connect()
            self._sim = sim
        return self._sim

    async def execute_location_cmd(self, lat, lon):
        try:
            sim = await self._get_sim()
            await sim.set(lat, lon)
        except Exception as e:
            print(f"[!] Location push failed: {e}, reconnecting...")
            global rsd
            rsd = None
            try:
                sim = await self._get_sim(fresh=True)
                await sim.set(lat, lon)
            except Exception as e2:
                print(f"[!] Reconnect also failed: {e2}")

    async def clear_location(self):
        global rsd
        try:
            sim = await self._get_sim(fresh=True)
            await sim.clear()
            print("[✓] Location cleared")
        except Exception as e:
            print(f"[!] Failed to clear location: {e}")
            rsd = None
            self._sim = None

    async def stop_and_clear(self):
        self.running = False
        self.paused = False
        if self.current_task and not self.current_task.done():
            self.current_task.cancel()
            try:
                await self.current_task
            except asyncio.CancelledError:
                pass
        self.current_task = None
        self.current_pos = None
        await self.clear_location()

    async def run_route(self, coordinates, speed_mph):
        self.running = True
        self.paused = False
        meters_per_sec = speed_mph * 0.44704

        for i in range(len(coordinates) - 1):
            if not self.running: break
            while self.paused:
                await asyncio.sleep(0.5)
                if not self.running: break

            p1, p2 = coordinates[i], coordinates[i+1]
            self.current_pos = {"lat": p1[1], "lon": p1[0]}

            lat_dist = (p2[1] - p1[1]) * 111139
            lon_dist = (p2[0] - p1[0]) * 92620
            distance = (lat_dist**2 + lon_dist**2)**0.5
            wait_time = distance / meters_per_sec if meters_per_sec > 0 else 1

            await self.execute_location_cmd(p1[1], p1[0])
            await asyncio.sleep(max(wait_time, 0.5))

        self.running = False
        self.current_pos = None


route_mgr = RouteManager()


@app.get("/")
async def index():
    return FileResponse('index.html', headers={
        "Cache-Control": "no-cache, no-store, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0"
    })

@app.get("/status")
async def get_status():
    return {"active_pos": route_mgr.current_pos, "running": route_mgr.running, "paused": route_mgr.paused}

@app.get("/set-location")
async def set_loc(lat: float, lon: float, background_tasks: BackgroundTasks):
    route_mgr.current_pos = {"lat": lat, "lon": lon}
    background_tasks.add_task(route_mgr.execute_location_cmd, lat, lon)
    return {"status": "success"}

@app.get("/reset-location")
async def reset_loc(background_tasks: BackgroundTasks):
    background_tasks.add_task(route_mgr.stop_and_clear)
    return {"status": "success"}

@app.post("/start-route")
async def start_route(data: dict):
    if route_mgr.current_task and not route_mgr.current_task.done():
        route_mgr.current_task.cancel()
    route_mgr.current_task = asyncio.create_task(route_mgr.run_route(data['coords'], data['speed']))
    return {"status": "started"}

@app.get("/pause-route")
async def pause_route():
    route_mgr.paused = not route_mgr.paused
    return {"paused": route_mgr.paused}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, access_log=False)
