import redis
from typing import Optional
import time

class RedisLock:
    def __init__(self, host='localhost', port=6379, db=0):
        """Inicializa la conexión con Redis"""
        self.redis_client = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.lock_timeout = 10  # segundos
    
    def acquire_lock(self, key: str, timeout: int = None) -> bool:
        """
        Intenta adquirir un lock
        Retorna True si se adquirió, False si está bloqueado
        """
        if timeout is None:
            timeout = self.lock_timeout
        
        # Usa SET con NX (solo si no existe) y EX (expira en X segundos)
        result = self.redis_client.set(
            f"lock:{key}",
            "locked",
            nx=True,
            ex=timeout
        )
        return result is not None
    
    def release_lock(self, key: str) -> bool:
        """Libera un lock"""
        return self.redis_client.delete(f"lock:{key}") > 0
    
    def is_locked(self, key: str) -> bool:
        """Verifica si una clave está bloqueada"""
        return self.redis_client.exists(f"lock:{key}") > 0
    
    def set_state(self, key: str, value: dict) -> None:
        """Guarda estado en Redis"""
        import json
        self.redis_client.set(f"state:{key}", json.dumps(value))
    
    def get_state(self, key: str) -> Optional[dict]:
        """Obtiene estado de Redis"""
        import json
        data = self.redis_client.get(f"state:{key}")
        if data:
            return json.loads(data)
        return None

# Instancia global
redis_lock = RedisLock()
