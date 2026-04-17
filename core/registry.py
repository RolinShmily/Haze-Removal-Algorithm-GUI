"""
算法注册表

提供数据驱动的算法管理机制，新增算法只需在算法文件末尾注册即可，
无需修改 UI 层任何代码。
"""

from dataclasses import dataclass, field
from typing import Callable, List, Dict, Optional


@dataclass
class ParamDef:
    """
    算法参数定义

    用于描述算法的一个可调参数（对应 UI 上的一个滑块或下拉框）。
    """
    name: str
    label: str
    type: str  # "int" | "float" | "choice"
    min_val: float = 0.0
    max_val: float = 1.0
    default: float = 0.5
    step: float = 1.0
    decimals: int = 0
    choices: list = field(default_factory=list)
    odd_only: bool = False


@dataclass
class AlgorithmDescriptor:
    """
    算法描述符

    描述一个去雾算法的完整元数据，包括分类、入口函数和参数列表。
    """
    id: str
    name: str
    description: str
    category: str  # "physical" | "enhancement" | "improved"
    func: Callable
    params: List[ParamDef]


class AlgorithmRegistry:
    """
    算法注册表（单例模式）
    """
    _algorithms: Dict[str, AlgorithmDescriptor] = {}

    @classmethod
    def register(cls, descriptor: AlgorithmDescriptor) -> None:
        """注册一个算法描述符"""
        cls._algorithms[descriptor.id] = descriptor

    @classmethod
    def get(cls, algo_id: str) -> Optional[AlgorithmDescriptor]:
        """获取指定 ID 的算法描述符"""
        return cls._algorithms.get(algo_id)

    @classmethod
    def all_algorithms(cls) -> List[AlgorithmDescriptor]:
        """获取所有已注册算法，按注册顺序返回"""
        return list(cls._algorithms.values())

    @classmethod
    def clear(cls) -> None:
        """清空注册表（仅用于测试）"""
        cls._algorithms.clear()
