from multiprocessing import Process,Queue
import asyncio
import psutil, os

def set_cpu(core_id:int) -> None:
    """Bind current process to a specific CPU core.
       value must be in range 0 to 7 according to your number of cores"""
    p = psutil.Process(os.getpid())
    p.cpu_affinity([core_id])
    print(f"Process {os.getpid()} assigned to CPU core {core_id}")

def run_binance_ws(queue) -> None:
    ' bind with core 1'
    set_cpu(1)  
    from wsocket import BinanceWS 
    ws = BinanceWS(queue)
    asyncio.run(ws.listen())

def run_bybit_ws(queue) -> None:
    ' bind with core 3'
    set_cpu(3)  
    from wsocket import BybitWS
    ws = BybitWS(queue)
    asyncio.run(ws.listen())

def run_storage(queue) -> None: 
    ' bind with core 2'
    set_cpu(2) 
    from decision import DecisionEngine  
    ds = DecisionEngine(queue)
    asyncio.run(ds.feed())

if __name__ == "__main__":
    pipeline = Queue()
    
    # meta data refill
    from binanceMeta import BINANCEExchangeInfo
    binance = BINANCEExchangeInfo(pipeline)
    binance.send_request()

    from bybitMeta import BYBITExchangeInfo
    bybit = BYBITExchangeInfo(pipeline)
    bybit.send_request()
    
    # multiprocessor handling
    processes = [
        Process(target=run_binance_ws, args=(pipeline,)),
        Process(target=run_bybit_ws, args=(pipeline,)),
        Process(target=run_storage, args=(pipeline,))
    ]
    # process start
    for p in processes:
        p.start()
    
    # wait for process end
    for p in processes:
        p.join()
