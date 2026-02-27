import { motion } from 'framer-motion'
import { pageTransition } from './variants'

export default function AnimatedPage({ children }) {
    return (
        <motion.div
            initial={pageTransition.initial}
            animate={pageTransition.animate}
            exit={pageTransition.exit}
            className="w-full"
        >
            {children}
        </motion.div>
    )
}
