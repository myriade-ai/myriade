from typing import List, Literal, Optional, Union

from pydantic import BaseModel


class GridOptions(BaseModel):
    left: Union[str, int] = "10%"
    right: Union[str, int] = "10%"
    bottom: Union[str, int] = "10%"
    top: Union[str, int] = "10%"
    containLabel: bool = True


class TitleOptions(BaseModel):
    text: str
    left: Union[str, Literal["center", "left", "right"]] = "center"


class AxisLabel(BaseModel):
    interval: int = 0
    rotate: Optional[int] = None
    formatter: Optional[str] = None


class Axis(BaseModel):
    type: Literal["value", "category", "time", "log"]
    name: Optional[str] = None
    min: Optional[Union[int, float]] = None
    max: Optional[Union[int, float]] = None
    inverse: Optional[bool] = None
    axisLabel: Optional[AxisLabel] = None


class SeriesLabel(BaseModel):
    show: bool = False
    position: str = "right"
    formatter: Optional[str] = None


class SeriesEncode(BaseModel):
    x: Optional[str] = None
    y: Optional[str] = None
    itemName: Optional[str] = None
    value: Optional[str] = None


class ItemStyle(BaseModel):
    color: Optional[str] = None


class Series(BaseModel):
    type: Literal["bar", "line", "pie", "scatter"]
    label: Optional[SeriesLabel] = None
    encode: SeriesEncode
    itemStyle: Optional[ItemStyle] = None


class Tooltip(BaseModel):
    trigger: Literal["item", "axis"] = "item"
    formatter: Optional[str] = None


class DataZoom(BaseModel):
    type: Literal["inside", "slider"]
    start: int = 0
    end: int = 100


class ChartOptions(BaseModel):
    grid: Optional[GridOptions] = None
    title: Optional[TitleOptions] = None
    xAxis: Axis
    yAxis: Axis
    series: List[Series]
    tooltip: Optional[Tooltip] = None
    dataZoom: Optional[List[DataZoom]] = None
