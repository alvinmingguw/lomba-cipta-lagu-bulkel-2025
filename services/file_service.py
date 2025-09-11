# -*- coding: utf-8 -*-
"""
File Service - Handles file storage and retrieval operations
Supports both Supabase Storage and legacy Google Drive
"""

import streamlit as st
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple, Union
import os
import io
import base64
import mimetypes
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileService:
    """Centralized file service for all file operations"""
    
    def __init__(self):
        """Initialize file service"""
        self.supabase_url = st.secrets.get("supabase_url")
        self.supabase_key = st.secrets.get("supabase_anon_key")
        self.storage_bucket = "song-contest-files"
        self._client = None
        
    @property
    def client(self):
        """Lazy initialization of Supabase client"""
        if self._client is None:
            try:
                from supabase import create_client
                self._client = create_client(self.supabase_url, self.supabase_key)
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {e}")
                st.error("File service connection failed. Please check configuration.")
                return None
        return self._client
    
    # ==================== UPLOAD OPERATIONS ====================
    
    def upload_file(self, file_content: bytes, file_name: str, 
                   file_type: str = None, folder: str = None) -> Optional[str]:
        """
        Upload file to Supabase Storage
        
        Args:
            file_content: File content as bytes
            file_name: Original file name
            file_type: File type ('audio', 'pdf', 'image')
            folder: Optional folder path
            
        Returns:
            File ID if successful, None otherwise
        """
        try:
            # Generate unique file path
            if folder:
                file_path = f"{folder}/{file_name}"
            else:
                file_path = file_name
            
            # Upload to Supabase Storage
            response = self.client.storage.from_(self.storage_bucket).upload(
                file_path, file_content
            )
            
            if response.get('error'):
                logger.error(f"Upload error: {response['error']}")
                return None
            
            # Store metadata in database
            file_id = self._store_file_metadata(
                file_path, file_name, file_type, len(file_content)
            )
            
            return file_id
            
        except Exception as e:
            logger.error(f"Error uploading file {file_name}: {e}")
            return None
    
    def _store_file_metadata(self, file_path: str, original_filename: str,
                           file_type: str, file_size_bytes: int) -> str:
        """Store file metadata - simplified without database table"""
        try:
            # Skip database storage since file_metadata table doesn't exist
            logger.info(f"File metadata storage skipped for {original_filename} - table not available")
            return file_path

        except Exception as e:
            logger.error(f"Error in file metadata handling: {e}")
            return file_path
    
    # ==================== DOWNLOAD OPERATIONS ====================
    
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_file_content(_self, file_id: str) -> Optional[bytes]:
        """Get file content from Supabase Storage"""
        try:
            response = _self.client.storage.from_(_self.storage_bucket).download(file_id)
            return response
        except Exception as e:
            logger.error(f"Error downloading file {file_id}: {e}")
            return None
    
    @st.cache_data(ttl=3600, show_spinner=False)
    def get_file_url(_self, file_id: str, expires_in: int = 3600) -> Optional[str]:
        """Get signed URL for file access"""
        try:
            response = _self.client.storage.from_(_self.storage_bucket).create_signed_url(
                file_id, expires_in
            )
            return response.get('signedURL')
        except Exception as e:
            logger.error(f"Error creating signed URL for {file_id}: {e}")
            return None
    
    def get_public_url(self, file_id: str) -> Optional[str]:
        """Get public URL for file (if bucket is public)"""
        try:
            response = self.client.storage.from_(self.storage_bucket).get_public_url(file_id)
            return response
        except Exception as e:
            logger.error(f"Error getting public URL for {file_id}: {e}")
            return None
    
    # ==================== LEGACY SUPPORT ====================
    
    def migrate_from_local(self, local_path: str, file_type: str = None) -> Optional[str]:
        """Migrate file from local storage to Supabase"""
        try:
            if not os.path.exists(local_path):
                logger.warning(f"Local file not found: {local_path}")
                return None
            
            with open(local_path, 'rb') as f:
                file_content = f.read()
            
            file_name = os.path.basename(local_path)
            
            # Determine file type from extension if not provided
            if not file_type:
                ext = Path(local_path).suffix.lower()
                if ext in ['.mp3', '.m4a', '.wav']:
                    file_type = 'audio'
                elif ext in ['.pdf']:
                    file_type = 'pdf'
                elif ext in ['.png', '.jpg', '.jpeg']:
                    file_type = 'image'
                else:
                    file_type = 'other'
            
            return self.upload_file(file_content, file_name, file_type, 'files')
            
        except Exception as e:
            logger.error(f"Error migrating file {local_path}: {e}")
            return None
    
    def batch_migrate_folder(self, folder_path: str, file_type: str = None) -> Dict[str, str]:
        """Migrate all files from a folder to Supabase"""
        results = {}
        
        if not os.path.exists(folder_path):
            logger.warning(f"Folder not found: {folder_path}")
            return results
        
        for file_name in os.listdir(folder_path):
            file_path = os.path.join(folder_path, file_name)
            
            if os.path.isfile(file_path):
                file_id = self.migrate_from_local(file_path, file_type)
                results[file_name] = file_id
                
                if file_id:
                    logger.info(f"Migrated: {file_name} -> {file_id}")
                else:
                    logger.error(f"Failed to migrate: {file_name}")
        
        return results
    
    # ==================== UTILITY FUNCTIONS ====================
    
    def get_file_info(self, file_id: str) -> Optional[Dict]:
        """Get file metadata - simplified without database table"""
        try:
            # Skip database lookup since file_metadata table doesn't exist
            logger.info(f"File info lookup skipped for {file_id} - table not available")
            return None

        except Exception as e:
            logger.error(f"Error in file info handling: {e}")
            return None
    
    def delete_file(self, file_id: str) -> bool:
        """Delete file from storage - simplified without database table"""
        try:
            # Delete from storage only
            self.client.storage.from_(self.storage_bucket).remove([file_id])

            # Skip database deletion since file_metadata table doesn't exist
            logger.info(f"File metadata deletion skipped for {file_id} - table not available")

            # Clear cache
            st.cache_data.clear()

            return True
            
        except Exception as e:
            logger.error(f"Error deleting file {file_id}: {e}")
            return False
    
    def list_files(self, file_type: str = None, folder: str = None) -> List[Dict]:
        """List files - simplified without database table"""
        try:
            # Skip database lookup since file_metadata table doesn't exist
            logger.info(f"File listing skipped - table not available")
            return []

        except Exception as e:
            logger.error(f"Error in file listing: {e}")
            return []

# Global instance
file_service = FileService()
