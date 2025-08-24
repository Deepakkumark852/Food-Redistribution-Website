<template>
  <div>
    <label class="form-label">Food Image (optional)</label>
    <input type="file" accept="image/*" @change="onFileChange" class="form-control" />
    <div v-if="preview" class="mt-2">
      <img :src="preview" alt="Preview" style="max-width:160px; max-height:160px; border-radius:8px; object-fit:cover;" />
      <button class="btn btn-sm btn-outline-danger ms-2" @click="removeImage" type="button">Remove</button>
    </div>
  </div>
</template>
<script setup>
import { ref, watch, defineEmits, defineProps } from 'vue';
const emit = defineEmits(['update:modelValue']);
const props = defineProps({ modelValue: String });
const preview = ref(props.modelValue ? `data:image/jpeg;base64,${props.modelValue}` : '');
watch(() => props.modelValue, v => {
  preview.value = v ? `data:image/jpeg;base64,${v}` : '';
});
function onFileChange(e) {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = ev => {
    const base64 = ev.target.result.split(',')[1];
    emit('update:modelValue', base64);
    preview.value = ev.target.result;
  };
  reader.readAsDataURL(file);
}
function removeImage() {
  emit('update:modelValue', '');
  preview.value = '';
}
</script>
