import jwt, { JwtPayload } from 'jsonwebtoken';
import 'dotenv/config';


const SECRET = process.env.JWT_SECRET ?? "dev-secret"
const ACCESS_TOKEN_TTL_MINUTES = Number(process.env.ACCESS_TOKEN_TTL_MINUTES ?? 15)


export function createToken(user: string): string {
    return jwt.sign({
            sub: user,
        },
        SECRET,
        { expiresIn: ACCESS_TOKEN_TTL_MINUTES * 60 }
    );
}


export function verifyToken(token: string): string {
    const payload = jwt.verify(token, SECRET) as JwtPayload
    if (typeof payload.sub !== 'string') throw new Error('invalid token payload');
    return payload.sub;
}
