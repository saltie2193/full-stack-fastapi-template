import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { AxiosError } from "axios"
import { useState } from "react"
import {
  type Body_login_login_access_token as AccessToken,
  type ApiError,
  LoginService,
  type UserRegister,
  UsersService,
} from "../client"
import { usersKeys } from "../queries/users.ts"
import { isLoggedIn, updateLocalAuthState } from "../utils/auth.ts"
import { useCurrentUser } from "./useCurrentUser.ts"
import useCustomToast from "./useCustomToast"

const useAuth = () => {
  const [error, setError] = useState<string | null>(null)
  const navigate = useNavigate()
  const showToast = useCustomToast()
  const queryClient = useQueryClient()
  const { user, isLoading } = useCurrentUser({ enabled: isLoggedIn() })

  const signUpMutation = useMutation({
    mutationFn: (data: UserRegister) =>
      UsersService.registerUser({ requestBody: data }),

    onSuccess: () => {
      navigate({ to: "/login" })
      showToast(
        "Account created.",
        "Your account has been created successfully.",
        "success",
      )
    },
    onError: (err: ApiError) => {
      let errDetail = (err.body as any)?.detail

      if (err instanceof AxiosError) {
        errDetail = err.message
      }

      showToast("Something went wrong.", errDetail, "error")
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] })
    },
  })

  const login = async (data: AccessToken) => {
    const response = await LoginService.loginAccessToken({
      formData: data,
    })
    updateLocalAuthState(response.access_token)
  }

  const loginMutation = useMutation({
    mutationFn: login,
    onSuccess: () => {
      navigate({ to: "/" })
    },
    onError: (err: ApiError) => {
      let errDetail = (err.body as any)?.detail

      if (err instanceof AxiosError) {
        errDetail = err.message
      }

      if (Array.isArray(errDetail)) {
        errDetail = "Something went wrong"
      }

      setError(errDetail)
    },
  })

  const logout = () => {
    updateLocalAuthState(null)
    queryClient.invalidateQueries({ queryKey: usersKeys.current() })
    navigate({ to: "/login" })
  }

  return {
    signUpMutation,
    loginMutation,
    logout,
    user,
    isLoading,
    error,
    resetError: () => setError(null),
  }
}

export default useAuth
