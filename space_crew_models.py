"""
Data models and interfaces for the Real-Time Space Crew Tracker.

This module contains the core data structures used throughout the space crew tracking system,
including crew member information, mission data, and data source interfaces.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class CrewStatus(Enum):
    """Status of a crew member in space."""
    ACTIVE = "active"
    RETURNING = "returning"
    UNKNOWN = "unknown"


class ValidationStatus(Enum):
    """Status of data validation from sources."""
    VALIDATED = "validated"
    PENDING = "pending"
    CONFLICTED = "conflicted"
    FAILED = "failed"


@dataclass
class CrewMember:
    """Represents an individual astronaut or cosmonaut currently in space."""
    id: str
    name: str
    nationality: str
    agency: str
    current_vehicle: str
    launch_date: datetime
    expected_return: Optional[datetime]
    mission_duration_days: int
    profile_image_url: Optional[str]
    status: CrewStatus

    def __post_init__(self):
        """Validate crew member data after initialization."""
        if not self.id or not self.name:
            raise ValueError("Crew member must have valid id and name")
        if not self.agency or not self.current_vehicle:
            raise ValueError("Crew member must have valid agency and current vehicle")
        if self.mission_duration_days < 0:
            raise ValueError("Mission duration cannot be negative")


@dataclass
class MissionData:
    """Information about active space missions."""
    mission_id: str
    mission_name: str
    agency: str
    launch_date: datetime
    expected_duration_days: int
    mission_objectives: List[str]
    spacecraft: str
    destination: str  # ISS, Tiangong, etc.

    def __post_init__(self):
        """Validate mission data after initialization."""
        if not self.mission_id or not self.mission_name:
            raise ValueError("Mission must have valid id and name")
        if not self.agency or not self.spacecraft:
            raise ValueError("Mission must have valid agency and spacecraft")
        if self.expected_duration_days <= 0:
            raise ValueError("Mission duration must be positive")
        if not self.destination:
            raise ValueError("Mission must have a valid destination")


@dataclass
class DataFreshness:
    """Tracks the freshness and validation status of data from sources."""
    last_update: datetime
    source_name: str
    confidence_level: float  # 0.0 to 1.0
    validation_status: ValidationStatus
    next_refresh: datetime

    def __post_init__(self):
        """Validate data freshness information after initialization."""
        if not self.source_name:
            raise ValueError("Source name cannot be empty")
        if not (0.0 <= self.confidence_level <= 1.0):
            raise ValueError("Confidence level must be between 0.0 and 1.0")
        if self.next_refresh <= self.last_update:
            raise ValueError("Next refresh must be after last update")

    @property
    def is_stale(self) -> bool:
        """Check if data is considered stale (older than 12 hours)."""
        from datetime import timedelta
        return datetime.now() - self.last_update > timedelta(hours=12)

    @property
    def hours_since_update(self) -> float:
        """Calculate hours since last update."""
        delta = datetime.now() - self.last_update
        return delta.total_seconds() / 3600


class SpaceDataSource(ABC):
    """Abstract base class for space agency data sources."""

    @abstractmethod
    def get_current_crew(self) -> List[CrewMember]:
        """
        Retrieve current crew members from the data source.
        
        Returns:
            List of CrewMember objects representing astronauts currently in space.
            
        Raises:
            ConnectionError: If unable to connect to the data source.
            ValueError: If the response data is invalid or malformed.
        """
        pass

    @abstractmethod
    def get_mission_details(self, mission_id: str) -> MissionData:
        """
        Retrieve detailed mission information for a specific mission.
        
        Args:
            mission_id: Unique identifier for the mission.
            
        Returns:
            MissionData object with detailed mission information.
            
        Raises:
            ConnectionError: If unable to connect to the data source.
            ValueError: If mission_id is invalid or mission not found.
        """
        pass

    @abstractmethod
    def validate_connection(self) -> bool:
        """
        Test the connection to the data source.
        
        Returns:
            True if connection is successful, False otherwise.
        """
        pass

    @abstractmethod
    def get_last_update_time(self) -> datetime:
        """
        Get the timestamp of the last data update from the source.
        
        Returns:
            Datetime of the last update from this source.
            
        Raises:
            ConnectionError: If unable to retrieve update information.
        """
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """
        Get the name of this data source.
        
        Returns:
            Human-readable name of the data source (e.g., "NASA ISS API").
        """
        pass

    @property
    @abstractmethod
    def base_url(self) -> str:
        """
        Get the base URL for this data source.
        
        Returns:
            Base URL string for the API endpoint.
        """
        pass


@dataclass
class RefreshResult:
    """Result of a data refresh operation."""
    success: bool
    updated_crew_count: int
    errors: List[str]
    refresh_time: datetime
    sources_updated: List[str]

    def __post_init__(self):
        """Validate refresh result data."""
        if self.updated_crew_count < 0:
            raise ValueError("Updated crew count cannot be negative")


@dataclass
class ValidationResult:
    """Result of data validation across multiple sources."""
    is_valid: bool
    confidence_score: float
    conflicting_sources: List[str]
    validation_time: datetime
    details: str

    def __post_init__(self):
        """Validate validation result data."""
        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")