"use client";

import { Modal, ModalFooter, ModalHeader, ModalTitle } from "./modal";
import { Button } from "./button";

interface DialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "primary";
  loading?: boolean;
}

export function Dialog({
  open,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "primary",
  loading,
}: DialogProps) {
  return (
    <Modal open={open} onClose={onClose} size="sm">
      <ModalHeader>
        <ModalTitle>{title}</ModalTitle>
      </ModalHeader>
      {description && <p className="text-sm text-gray-500">{description}</p>}
      <ModalFooter>
        <Button variant="secondary" onClick={onClose} disabled={loading}>
          {cancelLabel}
        </Button>
        <Button
          variant={variant === "danger" ? "danger" : "primary"}
          onClick={onConfirm}
          loading={loading}
        >
          {confirmLabel}
        </Button>
      </ModalFooter>
    </Modal>
  );
}
