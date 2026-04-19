from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class IncomingMessage:
    """
    Platform-agnostic representation of an inbound message.
    The webhook handler normalizes any platform's payload into this shape
    before the rest of the system ever touches it.
    """
    chat_id: str    # Unique identifier for the user/chat (Telegram chat_id, Twilio phone, etc.)
    body: str       # The text content of the message
    platform: str   # "telegram" | "sms" | "whatsapp"
    raw: dict = field(default_factory=dict)  # Original payload, useful for debugging


class BaseMessenger(ABC):
    """
    Abstract base class for messaging platforms.

    To add a new platform (e.g. WhatsApp, SMS), create a subclass
    in this folder and implement these four methods. The rest of the
    system — engine, tasks, webhooks — never needs to change.
    """

    @abstractmethod
    def validate_request(self, headers: dict, body: bytes) -> bool:
        """Verify the request genuinely came from the platform (not spoofed)."""
        pass

    @abstractmethod
    def parse_incoming(self, data: dict) -> IncomingMessage:
        """Normalize the platform's raw payload into an IncomingMessage."""
        pass

    @abstractmethod
    def send_message(self, chat_id: str, body: str) -> None:
        """Send a message to a user on this platform."""
        pass

    @abstractmethod
    def empty_response(self) -> dict:
        """
        Return the appropriate empty HTTP response for this platform.
        Used when we acknowledge receipt but reply asynchronously.
        """
        pass
