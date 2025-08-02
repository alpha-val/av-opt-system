import { AppBar, Toolbar, Typography, Box } from "@mui/material";
import React from "react";

const Nav = () => {
    return (
        <>
            <AppBar position="static">
                <Toolbar>
                    <Typography variant="h6" component="a" href="/" sx={{ textDecoration: 'none', color: 'inherit', letterSpacing: 1.25, fontWeight: 600 }}>
                        OptPro
                    </Typography>
                </Toolbar>
            </AppBar>
        </>
    );
};

export default Nav;