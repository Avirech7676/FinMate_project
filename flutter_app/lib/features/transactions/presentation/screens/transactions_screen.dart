import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../../core/utils/formatters.dart';
import '../../../../shared/models/transaction.dart';
import '../transaction_providers.dart';

class TransactionsScreen extends ConsumerStatefulWidget {
  const TransactionsScreen({super.key});

  @override
  ConsumerState<TransactionsScreen> createState() => _TransactionsScreenState();
}

class _TransactionsScreenState extends ConsumerState<TransactionsScreen> {
  String _selectedCategory = 'All';
  String _searchQuery = '';
  final _searchController = TextEditingController();

  final List<String> _categories = [
    'All',
    'Food',
    'Housing',
    'Transportation',
    'Utilities',
    'Entertainment',
    'Healthcare',
    'Income',
  ];

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _showAddTransactionDialog() {
    final amountController = TextEditingController();
    final descController = TextEditingController();
    String category = 'Food';
    bool isIncome = false;

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          backgroundColor: const Color(0xFF1E293B),
          title: const Text('Add Transaction', style: TextStyle(color: Colors.white)),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                TextField(
                  controller: descController,
                  decoration: const InputDecoration(labelText: 'Description / Merchant'),
                ),
                const SizedBox(height: 12),
                TextField(
                  controller: amountController,
                  keyboardType: const TextInputType.numberWithOptions(decimal: true),
                  decoration: const InputDecoration(labelText: 'Amount (\$)'),
                ),
                const SizedBox(height: 12),
                DropdownButtonFormField<String>(
                  value: category,
                  dropdownColor: const Color(0xFF1E293B),
                  items: _categories
                      .where((c) => c != 'All')
                      .map((c) => DropdownMenuItem(value: c, child: Text(c)))
                      .toList(),
                  onChanged: (v) => setDialogState(() => category = v!),
                  decoration: const InputDecoration(labelText: 'Category'),
                ),
                const SizedBox(height: 12),
                SwitchListTile(
                  title: const Text('Is Income?', style: TextStyle(color: Colors.white70)),
                  value: isIncome,
                  activeColor: const Color(0xFF10B981),
                  onChanged: (v) => setDialogState(() => isIncome = v),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel'),
            ),
            ElevatedButton(
              onPressed: () {
                final amount = double.tryParse(amountController.text) ?? 0.0;
                final desc = descController.text.trim();
                if (amount > 0 && desc.isNotEmpty) {
                  final filter = (
                    selectedCategory: _selectedCategory,
                    searchQuery: _searchQuery,
                    page: 1,
                  );
                  ref.read(transactionListNotifierProvider(filter).notifier).createTransaction(
                        amount: amount,
                        category: category,
                        description: desc,
                        date: DateTime.now(),
                        isIncome: isIncome,
                      );
                  Navigator.pop(ctx);
                }
              },
              child: const Text('Save'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final filter = (
      selectedCategory: _selectedCategory,
      searchQuery: _searchQuery,
      page: 1,
    );

    final txAsync = ref.watch(transactionListNotifierProvider(filter));

    return Scaffold(
      backgroundColor: const Color(0xFF090D16),
      appBar: AppBar(
        title: const Text('Transactions'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add_rounded),
            tooltip: 'Add Transaction',
            onPressed: _showAddTransactionDialog,
          ),
        ],
      ),
      body: Column(
        children: [
          // Search Bar
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Search transactions...',
                prefixIcon: const Icon(Icons.search_rounded),
                suffixIcon: _searchQuery.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear_rounded),
                        onPressed: () {
                          _searchController.clear();
                          setState(() => _searchQuery = '');
                        },
                      )
                    : null,
              ),
              onChanged: (val) => setState(() => _searchQuery = val),
            ),
          ),

          // Category Chips Filter
          SizedBox(
            height: 44,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 16),
              itemCount: _categories.length,
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (context, index) {
                final cat = _categories[index];
                final isSelected = cat == _selectedCategory;
                return ChoiceChip(
                  label: Text(cat),
                  selected: isSelected,
                  selectedColor: const Color(0xFF6366F1),
                  backgroundColor: const Color(0xFF1E293B),
                  labelStyle: TextStyle(
                    color: isSelected ? Colors.white : const Color(0xFF94A3B8),
                    fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                  ),
                  onSelected: (_) => setState(() => _selectedCategory = cat),
                );
              },
            ),
          ),
          const SizedBox(height: 8),

          // Transaction List via ListView.builder
          Expanded(
            child: txAsync.when(
              data: (transactions) {
                if (transactions.isEmpty) {
                  return const Center(
                    child: Text(
                      'No transactions found.',
                      style: TextStyle(color: Color(0xFF94A3B8)),
                    ),
                  );
                }

                return ListView.builder(
                  itemCount: transactions.length,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  itemBuilder: (context, index) {
                    final tx = transactions[index];
                    return _TransactionTile(
                      transaction: tx,
                      onDelete: () {
                        ref
                            .read(transactionListNotifierProvider(filter).notifier)
                            .deleteTransaction(tx.id);
                      },
                    );
                  },
                );
              },
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (err, _) => Center(
                child: Text('Failed to load transactions: $err',
                    style: const TextStyle(color: Colors.red)),
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _TransactionTile extends StatelessWidget {
  final Transaction transaction;
  final VoidCallback onDelete;

  const _TransactionTile({
    required this.transaction,
    required this.onDelete,
  });

  @override
  Widget build(BuildContext context) {
    final isIncome = transaction.isIncome;
    final amountColor = isIncome ? const Color(0xFF10B981) : const Color(0xFFF1F5F9);
    final prefix = isIncome ? '+' : '-';

    return Dismissible(
      key: Key(transaction.id),
      direction: DismissDirection.endToStart,
      background: Container(
        alignment: Alignment.centerRight,
        padding: const EdgeInsets.symmetric(horizontal: 20),
        color: const Color(0xFFEF4444),
        child: const Icon(Icons.delete_outline_rounded, color: Colors.white),
      ),
      onDismissed: (_) => onDelete(),
      child: Container(
        margin: const EdgeInsets.only(bottom: 8),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        decoration: BoxDecoration(
          color: const Color(0xFF1E293B),
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: const Color(0xFF334155), width: 0.8),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: isIncome
                    ? const Color(0xFF10B981).withOpacity(0.12)
                    : const Color(0xFF6366F1).withOpacity(0.12),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(
                isIncome ? Icons.south_west_rounded : Icons.north_east_rounded,
                size: 18,
                color: isIncome ? const Color(0xFF10B981) : const Color(0xFF818CF8),
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    transaction.description,
                    style: const TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      color: Color(0xFFF8FAFC),
                    ),
                  ),
                  const SizedBox(height: 2),
                  Row(
                    children: [
                      Text(
                        transaction.category,
                        style: const TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        Formatters.date(transaction.date),
                        style: const TextStyle(fontSize: 12, color: Color(0xFF64748B)),
                      ),
                      if (!transaction.isSynced) ...[
                        const SizedBox(width: 8),
                        const Icon(Icons.cloud_upload_outlined, size: 12, color: Color(0xFFF59E0B)),
                      ],
                    ],
                  ),
                ],
              ),
            ),
            Text(
              '$prefix${Formatters.currency(transaction.amount)}',
              style: TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w700,
                color: amountColor,
              ),
            ),
          ],
        ),
      ),
    );
  }
}
