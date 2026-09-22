import 'dart:convert';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart' as p;
import '../constants/app_constants.dart';
import '../errors/exceptions.dart';

/// Offline-first persistent storage using SQLite for queryable caching
/// and transaction synchronization queue.
class LocalCacheService {
  Database? _db;

  Future<Database> get database async {
    if (_db != null) return _db!;
    _db = await _initDatabase();
    return _db!;
  }

  Future<Database> _initDatabase() async {
    try {
      final dbPath = await getDatabasesPath();
      final path = p.join(dbPath, 'finmate_offline_cache.db');

      return await openDatabase(
        path,
        version: 1,
        onCreate: (db, version) async {
          // Key-Value cache table for screens (Overview, Health, Forecast)
          await db.execute('''
            CREATE TABLE key_value_cache (
              cache_key TEXT PRIMARY KEY,
              json_data TEXT NOT NULL,
              updated_at INTEGER NOT NULL
            )
          ''');

          // Local transactions cache table
          await db.execute('''
            CREATE TABLE cached_transactions (
              id TEXT PRIMARY KEY,
              amount REAL NOT NULL,
              category TEXT NOT NULL,
              description TEXT NOT NULL,
              date TEXT NOT NULL,
              is_income INTEGER NOT NULL,
              is_recurring INTEGER NOT NULL,
              sync_status TEXT NOT NULL
            )
          ''');

          // Offline sync queue table
          await db.execute('''
            CREATE TABLE offline_sync_queue (
              queue_id INTEGER PRIMARY KEY AUTOINCREMENT,
              action TEXT NOT NULL,
              endpoint TEXT NOT NULL,
              payload TEXT NOT NULL,
              created_at INTEGER NOT NULL
            )
          ''');
        },
      );
    } catch (e) {
      throw CacheException('Failed to initialize local SQLite database: $e');
    }
  }

  // Key-Value Cache Operations
  Future<void> cacheJson(String key, Map<String, dynamic> data) async {
    final db = await database;
    await db.insert(
      'key_value_cache',
      {
        'cache_key': key,
        'json_data': jsonEncode(data),
        'updated_at': DateTime.now().millisecondsSinceEpoch,
      },
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<(Map<String, dynamic>?, DateTime?)> getCachedJson(String key) async {
    final db = await database;
    final results = await db.query(
      'key_value_cache',
      where: 'cache_key = ?',
      whereArgs: [key],
      limit: 1,
    );
    if (results.isEmpty) return (null, null);

    final row = results.first;
    final jsonStr = row['json_data'] as String;
    final updatedAt = DateTime.fromMillisecondsSinceEpoch(row['updated_at'] as int);
    return (jsonDecode(jsonStr) as Map<String, dynamic>, updatedAt);
  }

  // Offline Sync Queue Operations
  Future<void> enqueueOfflineMutation({
    required String action,
    required String endpoint,
    required Map<String, dynamic> payload,
  }) async {
    final db = await database;
    await db.insert('offline_sync_queue', {
      'action': action,
      'endpoint': endpoint,
      'payload': jsonEncode(payload),
      'created_at': DateTime.now().millisecondsSinceEpoch,
    });
  }

  Future<List<Map<String, dynamic>>> getPendingSyncQueue() async {
    final db = await database;
    return await db.query('offline_sync_queue', orderBy: 'created_at ASC');
  }

  Future<void> removeSyncQueueItem(int queueId) async {
    final db = await database;
    await db.delete(
      'offline_sync_queue',
      where: 'queue_id = ?',
      whereArgs: [queueId],
    );
  }

  Future<void> clearAll() async {
    final db = await database;
    await db.delete('key_value_cache');
    await db.delete('cached_transactions');
    await db.delete('offline_sync_queue');
  }
}
