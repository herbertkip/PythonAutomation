import os
import sys
import json
import hashlib
from datetime import datetime
from pathlib import Path

class DirectoryMonitor:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.snapshot_file = self.directory / '.directory_snapshot.json'
        self.snapshot = {}
        self.load_snapshot()
    
    def get_file_hash(self, filepath):
        """Calculate MD5 hash of a file"""
        try:
            with open(filepath, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except (PermissionError, OSError):
            return None
    
    def scan_directory(self):
        """Scan directory and create a snapshot of current files"""
        current_files = {}
        
        if not self.directory.exists():
            print(f"Error: Directory '{self.directory}' does not exist!")
            return None
        
        try:
            for filepath in self.directory.rglob('*'):
                if filepath.is_file() and filepath.name != '.directory_snapshot.json':
                    relative_path = str(filepath.relative_to(self.directory))
                    stat = filepath.stat()
                    current_files[relative_path] = {
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'hash': self.get_file_hash(filepath)
                    }
        except PermissionError:
            print(f"Error: Permission denied to access some files in '{self.directory}'")
            return None
        
        return current_files
    
    def load_snapshot(self):
        """Load previous snapshot from file"""
        if self.snapshot_file.exists():
            try:
                with open(self.snapshot_file, 'r') as f:
                    data = json.load(f)
                    self.snapshot = data.get('files', {})
                    self.last_scan = data.get('last_scan', None)
            except (json.JSONDecodeError, IOError):
                self.snapshot = {}
                self.last_scan = None
        else:
            self.snapshot = {}
            self.last_scan = None
    
    def save_snapshot(self, current_files):
        """Save current snapshot to file"""
        data = {
            'files': current_files,
            'last_scan': datetime.now().isoformat()
        }
        
        try:
            with open(self.snapshot_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Warning: Could not save snapshot: {e}")
    
    def compare_snapshots(self, current_files):
        """Compare current files with previous snapshot"""
        if not self.snapshot:
            print("\n📁 First scan - creating baseline snapshot...")
            return [], [], []
        
        deleted_files = []
        new_files = []
        modified_files = []
        
        # Check for deleted files
        for filepath in self.snapshot:
            if filepath not in current_files:
                deleted_files.append({
                    'path': filepath,
                    'last_seen': self.last_scan
                })
        
        # Check for new files
        for filepath in current_files:
            if filepath not in self.snapshot:
                new_files.append({
                    'path': filepath,
                    'detected': datetime.now().isoformat()
                })
        
        # Check for modified files
        for filepath in current_files:
            if filepath in self.snapshot:
                old_info = self.snapshot[filepath]
                new_info = current_files[filepath]
                
                if (old_info['size'] != new_info['size'] or 
                    old_info['hash'] != new_info['hash']):
                    modified_files.append({
                        'path': filepath,
                        'old_size': old_info['size'],
                        'new_size': new_info['size'],
                        'detected': datetime.now().isoformat()
                    })
        
        return deleted_files, new_files, modified_files
    
    def display_results(self, deleted, new, modified):
        """Display results in command line"""
        print("\n" + "="*60)
        print(f"📊 Directory Scan Results for: {self.directory}")
        print("="*60)
        
        if deleted:
            print(f"\n❌ DELETED FILES ({len(deleted)}):")
            print("-"*40)
            for item in deleted:
                print(f"  • {item['path']}")
                if item['last_seen']:
                    last_seen = datetime.fromisoformat(item['last_seen'])
                    print(f"    Last seen: {last_seen.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("\n✅ No deleted files detected")
        
        if new:
            print(f"\n📄 NEW FILES ({len(new)}):")
            print("-"*40)
            for item in new:
                print(f"  • {item['path']}")
                detected = datetime.fromisoformat(item['detected'])
                print(f"    Detected: {detected.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if modified:
            print(f"\n✏️ MODIFIED FILES ({len(modified)}):")
            print("-"*40)
            for item in modified:
                print(f"  • {item['path']}")
                print(f"    Size: {item['old_size']} → {item['new_size']} bytes")
                detected = datetime.fromisoformat(item['detected'])
                print(f"    Detected: {detected.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print("\n" + "="*60)
    
    def run(self):
        """Main execution method"""
        current_files = self.scan_directory()
        
        if current_files is None:
            return False
        
        deleted, new, modified = self.compare_snapshots(current_files)
        self.display_results(deleted, new, modified)
        
        # Save current snapshot for next run
        self.save_snapshot(current_files)
        print(f"\n💾 Snapshot saved to: {self.snapshot_file}")
        
        return True

def main():
    print("="*60)
    print("📂 DIRECTORY DELETION MONITOR")
    print("="*60)
    
    # Prompt for directory
    while True:
        directory = input("\nEnter directory path to monitor: ").strip()
        
        # Remove quotes if present
        directory = directory.strip('"').strip("'")
        
        if not directory:
            print("❌ Error: Please enter a valid directory path")
            continue
        
        if not os.path.exists(directory):
            print(f"❌ Error: Directory '{directory}' does not exist")
            continue
        
        if not os.path.isdir(directory):
            print(f"❌ Error: '{directory}' is not a directory")
            continue
        
        break
    
    # Create monitor and run
    monitor = DirectoryMonitor(directory)
    
    try:
        success = monitor.run()
        if success:
            print("\n✨ Scan complete!")
    except KeyboardInterrupt:
        print("\n\n⚠️ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()