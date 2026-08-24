package main


import (
	"os"
	"fmt"
	"time"
	"github.com/golang-jwt/jwt/v5"
)


var jwtSecret = []byte(os.Getenv("JWT_SECRET"))

func createToken(user string) (string, error) {
	claims := jwt.MapClaims{
		"sub": user,
		"exp": time.Now().Add(15 * time.Minute).Unix(),
	}
	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(jwtSecret)
}

func verifyToken(tokenString string) (string, error) {
	token, err := jwt.Parse(tokenString, func(t *jwt.Token) (any, error) {
		return jwtSecret, nil
	})
	if err != nil {
		return "", err
	}
	claims, ok := token.Claims.(jwt.MapClaims)
	if !ok {
		return "", fmt.Errorf("Invalid claims")
	}
	sub, ok := claims["sub"].(string)
	if !ok {
		return "", fmt.Errorf(("no sub in token"))
	}
	return sub, nil
}