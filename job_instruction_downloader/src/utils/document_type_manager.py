"""
Document type configuration manager for universal document processing.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from .config import ConfigManager


class DocumentTypeManager:
    """Manages document type configurations and validation rules."""

    def __init__(self, config_manager: ConfigManager):
        """Initialize the document type manager.

        Args:
            config_manager: Configuration manager instance.
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        self._document_types = None

    @property
    def document_types(self) -> Dict[str, Any]:
        """Get all document type configurations.

        Returns:
            Dictionary of document type configurations.
        """
        if self._document_types is None:
            settings = self.config_manager.load_config()
            self._document_types = settings.get("document_types", {})
        return self._document_types

    def get_document_type_config(self, document_type: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific document type.

        Args:
            document_type: Type of document (e.g., 'job_instruction', 'contract').

        Returns:
            Document type configuration or None if not found.
        """
        return self.document_types.get(document_type)

    def get_supported_extensions(self, document_type: str) -> List[str]:
        """Get supported file extensions for a document type.

        Args:
            document_type: Type of document.

        Returns:
            List of supported file extensions.
        """
        config = self.get_document_type_config(document_type)
        if config:
            return config.get("supported_extensions", [])
        return []

    def get_default_extension(self, document_type: str) -> str:
        """Get default file extension for a document type.

        Args:
            document_type: Type of document.

        Returns:
            Default file extension.
        """
        config = self.get_document_type_config(document_type)
        if config:
            return config.get("default_extension", ".docx")
        return ".docx"

    def get_validation_config(self, document_type: str) -> Dict[str, Any]:
        """Get validation configuration for a document type.

        Args:
            document_type: Type of document.

        Returns:
            Validation configuration dictionary.
        """
        config = self.get_document_type_config(document_type)
        if config:
            return config.get("validation", {})
        return {}

    def get_folder_name(self, document_type: str) -> str:
        """Get folder name for a document type.

        Args:
            document_type: Type of document.

        Returns:
            Folder name for organizing documents.
        """
        config = self.get_document_type_config(document_type)
        if config:
            return config.get("folder_name", document_type.replace("_", " ").title())
        return document_type.replace("_", " ").title()

    def validate_document_type(self, document_type: str) -> bool:
        """Validate if a document type is supported.

        Args:
            document_type: Type of document to validate.

        Returns:
            True if document type is supported, False otherwise.
        """
        return document_type in self.document_types

    def get_available_document_types(self) -> List[str]:
        """Get list of all available document types.

        Returns:
            List of available document type keys.
        """
        return list(self.document_types.keys())

    def get_document_type_info(self, document_type: str) -> Dict[str, Any]:
        """Get human-readable information about a document type.

        Args:
            document_type: Type of document.

        Returns:
            Dictionary with name, description, and other info.
        """
        config = self.get_document_type_config(document_type)
        if config:
            return {
                "type": document_type,
                "name": config.get("name", ""),
                "description": config.get("description", ""),
                "default_extension": config.get("default_extension", ".docx"),
                "supported_extensions": config.get("supported_extensions", []),
                "folder_name": config.get("folder_name", "")
            }
        return {}

    def is_extension_supported(self, document_type: str, file_extension: str) -> bool:
        """Check if a file extension is supported for a document type.

        Args:
            document_type: Type of document.
            file_extension: File extension to check (e.g., '.pdf').

        Returns:
            True if extension is supported, False otherwise.
        """
        supported_extensions = self.get_supported_extensions(document_type)
        return file_extension.lower() in [ext.lower() for ext in supported_extensions]
