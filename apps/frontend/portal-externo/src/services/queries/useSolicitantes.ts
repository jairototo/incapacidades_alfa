import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { solicitantesApi } from '../api';
import type { SolicitanteCreate, SolicitanteUpdate, SearchSolicitanteParams } from '@/types/solicitante';

/**
 * Query Keys para Solicitantes
 */
export const solicitanteKeys = {
  all: ['solicitantes'] as const,
  search: (params: SearchSolicitanteParams) => ['solicitantes', 'search', params] as const,
  byId: (id: string) => ['solicitantes', id] as const,
};

/**
 * Hook para buscar solicitantes por correo (autocomplete)
 */
export function useSearchSolicitantes(
  params: SearchSolicitanteParams, 
  enabled: boolean = true
) {
  return useQuery({
    queryKey: solicitanteKeys.search(params),
    queryFn: async () => {
      const { data } = await solicitantesApi.search(params);
      return data;
    },
    enabled: enabled && params.correo.length >= 3, // Solo buscar si >=3 chars
    staleTime: 5 * 60 * 1000, // 5 minutos
    retry: 1,
  });
}

/**
 * Hook para obtener solicitante por ID
 */
export function useSolicitante(id: string, enabled: boolean = true) {
  return useQuery({
    queryKey: solicitanteKeys.byId(id),
    queryFn: async () => {
      const { data } = await solicitantesApi.getById(id);
      return data;
    },
    enabled: enabled && !!id,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Mutation para crear solicitante
 */
export function useCreateSolicitante() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (newSolicitante: SolicitanteCreate) => {
      const { data } = await solicitantesApi.create(newSolicitante);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: solicitanteKeys.all });
    },
  });
}

/**
 * Mutation para actualizar solicitante
 */
export function useUpdateSolicitante() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: SolicitanteUpdate }) => {
      const response = await solicitantesApi.update(id, data);
      return response.data;
    },
    onMutate: async ({ id, data }) => {
      // Cancelar queries en curso
      await queryClient.cancelQueries({ queryKey: solicitanteKeys.byId(id) });
      
      // Snapshot del valor previo
      const previousSolicitante = queryClient.getQueryData(solicitanteKeys.byId(id));
      
      // Optimistic update
      queryClient.setQueryData(solicitanteKeys.byId(id), (old: any) => ({
        ...old,
        ...data,
      }));
      
      return { previousSolicitante };
    },
    onError: (_error: any, variables, context) => {
      // Revertir optimistic update
      if (context?.previousSolicitante) {
        queryClient.setQueryData(
          solicitanteKeys.byId(variables.id),
          context.previousSolicitante
        );
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: solicitanteKeys.all });
    },
  });
}

/**
 * Mutation para eliminar solicitante
 */
export function useDeleteSolicitante() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (id: string) => {
      await solicitantesApi.delete(id);
      return id;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: solicitanteKeys.all });
    },
  });
}
