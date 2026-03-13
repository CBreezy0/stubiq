'use client';

import { useRouter } from 'next/navigation';

import { InventoryImportForm } from '@/components/InventoryImportForm';
import { RequireAuth } from '@/components/RequireAuth';

function InventoryImportPageContent() {
  const router = useRouter();

  return (
    <div className="space-y-6">
      <InventoryImportForm
        onImported={() => {
          router.replace('/inventory');
        }}
      />
    </div>
  );
}

export default function InventoryImportPage() {
  return (
    <RequireAuth>
      <InventoryImportPageContent />
    </RequireAuth>
  );
}
